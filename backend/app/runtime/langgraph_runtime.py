from datetime import UTC, datetime
from typing import Any, Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.runs import WorkflowRun
from app.runtime.llm import LLMClient
from app.runtime.state import WorkflowState
from app.runtime.tools import (
    calculate_fees,
    check_provider_health,
    check_risk_conditions,
    draft_chargeback_response,
    lookup_transaction,
    recommend_route,
    score_fraud_risk,
)
from app.services.agent_service import get_agents_by_node_binding
from app.services.run_service import (
    add_event,
    add_message,
    add_tool_execution,
    get_run,
    set_run_status,
)


class AgentRuntime:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.llm = LLMClient()

    async def execute_run(self, run_id: str) -> WorkflowRun:
        run = await get_run(self.session, run_id)
        if not run:
            raise ValueError(f"Workflow run not found: {run_id}")

        agent_configs = await get_agents_by_node_binding(self.session)

        await set_run_status(self.session, run, "running")
        await add_event(
            self.session,
            run_id=run.id,
            event_type="run_started",
            title="Workflow run started",
            body=f"Template {run.template_key} accepted a {run.channel} request.",
            node_id="start",
        )
        await self.session.commit()

        if "chargeback" in run.template_key:
            graph = self._build_chargeback_graph(agent_configs)
        else:
            graph = self._build_routing_graph(agent_configs)

        try:
            state = await graph.ainvoke(
                {
                    "run_id": run.id,
                    "template_key": run.template_key,
                    "user_message": run.input_message,
                    "agent_configs": agent_configs,
                    "token_count": 0,
                    "estimated_cost_usd": 0.0,
                    "messages": [],
                    "events": [],
                }
            )

            run = await get_run(self.session, run_id)
            if not run:
                raise ValueError(f"Run disappeared: {run_id}")

            status = "awaiting_approval" if state.get("needs_approval") else "completed"
            await set_run_status(
                self.session,
                run,
                status,
                final_response=state.get("final_response"),
                confidence=state.get("confidence"),
                token_count=state.get("token_count", 0),
                estimated_cost_usd=state.get("estimated_cost_usd", 0.0),
            )
            await add_event(
                self.session,
                run_id=run.id,
                event_type=status,
                title="Run completed" if status == "completed" else "Human approval required",
                body=state.get("final_response", "Workflow finished."),
                node_id="final",
                token_count=state.get("token_count", 0),
                cost_usd=state.get("estimated_cost_usd", 0.0),
            )
            await self.session.commit()
            return run

        except Exception as exc:
            run = await get_run(self.session, run_id)
            if run:
                await set_run_status(
                    self.session,
                    run,
                    "failed",
                    final_response=str(exc),
                )
                await add_event(
                    self.session,
                    run_id=run.id,
                    event_type="failed",
                    title="Workflow failed",
                    body=str(exc),
                    node_id="runtime",
                )
                await self.session.commit()
            raise

    # -----------------------------------------------------------------------
    # CHARGEBACK GRAPH
    # -----------------------------------------------------------------------

    def _build_chargeback_graph(self, agent_configs: dict[str, Any]):
        graph = StateGraph(WorkflowState)
        graph.add_node("triage_agent", self._make_triage_node(agent_configs))
        graph.add_node("resolution_agent", self._make_resolution_node(agent_configs))
        graph.add_node("approval_gate", self._approval_gate)
        graph.set_entry_point("triage_agent")
        graph.add_edge("triage_agent", "resolution_agent")
        graph.add_conditional_edges(
            "resolution_agent",
            self._route_after_resolution,
            {"approval": "approval_gate", "done": END},
        )
        graph.add_edge("approval_gate", END)
        return graph.compile()

    def _make_triage_node(self, agent_configs: dict[str, Any]):
        async def _triage_agent(state: WorkflowState) -> WorkflowState:
            run_id = state["run_id"]
            agent = agent_configs.get("triage_agent")
            system = (
                agent.system_prompt
                if agent
                else "You are a chargeback triage specialist for Yuno."
            )
            model = agent.model if agent else None
            guardrails = agent.guardrails if agent else []

            transaction_result = lookup_transaction(state["user_message"])
            transaction = transaction_result.output
            provider = transaction.get("provider", "Adyen")
            health_result = check_provider_health(transaction.get("country", "BR"))
            provider_health = health_result.output.get(provider, {})
            risk_result = score_fraud_risk(transaction, provider_health)
            fraud_risk = risk_result.output

            for result in [transaction_result, health_result, risk_result]:
                await add_tool_execution(
                    self.session,
                    run_id=run_id,
                    tool_name=result.name,
                    input=result.input,
                    output=result.output,
                    duration_ms=result.duration_ms,
                )

            guardrail_note = (
                f" Guardrails: {', '.join(guardrails)}." if guardrails else ""
            )
            fallback = draft_chargeback_response(transaction, fraud_risk)
            llm_result = await self.llm.complete(
                system=system + guardrail_note,
                prompt=(
                    f"User message: {state['user_message']}\n"
                    f"Transaction: {transaction}\n"
                    f"Fraud risk: {fraud_risk}\n"
                    f"Classify this chargeback and summarise findings for the resolution agent."
                ),
                fallback=fallback,
                model=model,
            )

            await add_message(
                self.session,
                run_id=run_id,
                sender="Chargeback Triage Agent",
                recipient="Resolution Agent",
                channel="agent",
                content=llm_result.text,
                payload={
                    "transaction_id": transaction.get("transaction_id"),
                    "fraud_score": fraud_risk.get("score"),
                },
            )
            await add_event(
                self.session,
                run_id=run_id,
                event_type="agent_decision",
                title="Triage Agent classified the chargeback",
                body=llm_result.text,
                node_id="triage-agent",
                token_count=llm_result.tokens,
                cost_usd=llm_result.cost_usd,
                payload={
                    "transaction": transaction,
                    "fraud_risk": fraud_risk,
                },
            )
            await self.session.commit()

            return {
                **state,
                "transaction": transaction,
                "fraud_risk": fraud_risk,
                "provider_health": provider_health,
                "transaction_id": transaction.get("transaction_id"),
                "merchant_name": transaction.get("merchant_name"),
                "country": transaction.get("country"),
                "currency": transaction.get("currency"),
                "amount": transaction.get("amount"),
                "token_count": state.get("token_count", 0) + llm_result.tokens,
                "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + llm_result.cost_usd,
            }

        return _triage_agent

    def _make_resolution_node(self, agent_configs: dict[str, Any]):
        async def _resolution_agent(state: WorkflowState) -> WorkflowState:
            run_id = state["run_id"]
            agent = agent_configs.get("resolution_agent")
            system = (
                agent.system_prompt
                if agent
                else "You are a payment resolution specialist for Yuno."
            )
            model = agent.model if agent else None
            guardrails = agent.guardrails if agent else []

            transaction = state.get("transaction", {})
            fraud_risk = state.get("fraud_risk", {})
            needs_approval = bool(fraud_risk.get("requires_human_approval"))

            guardrail_note = (
                f" Guardrails: {', '.join(guardrails)}." if guardrails else ""
            )
            fallback = draft_chargeback_response(transaction, fraud_risk)
            llm_result = await self.llm.complete(
                system=system + guardrail_note,
                prompt=(
                    f"User message: {state['user_message']}\n"
                    f"Transaction: {transaction}\n"
                    f"Fraud risk assessment: {fraud_risk}\n"
                    f"Draft a professional chargeback resolution response. "
                    f"Approval required: {needs_approval}."
                ),
                fallback=fallback,
                model=model,
            )

            recipient = "Human Approver" if needs_approval else "Merchant"
            await add_message(
                self.session,
                run_id=run_id,
                sender="Resolution Agent",
                recipient=recipient,
                channel="agent",
                content=llm_result.text,
                payload={"needs_approval": needs_approval},
            )
            await add_event(
                self.session,
                run_id=run_id,
                event_type="llm_generation",
                title="Resolution Agent drafted response",
                body=llm_result.text,
                node_id="resolution-agent",
                token_count=llm_result.tokens,
                cost_usd=llm_result.cost_usd,
            )
            await self.session.commit()

            return {
                **state,
                "final_response": llm_result.text,
                "needs_approval": needs_approval,
                "confidence": fraud_risk.get("confidence", 0.74),
                "token_count": state.get("token_count", 0) + llm_result.tokens,
                "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + llm_result.cost_usd,
            }

        return _resolution_agent

    async def _approval_gate(self, state: WorkflowState) -> WorkflowState:
        await add_event(
            self.session,
            run_id=state["run_id"],
            event_type="approval_gate",
            title="Human approval gate paused the workflow",
            body="High fraud risk detected. Operator approval required before sending response.",
            node_id="approval-gate",
            payload={"final_response": state.get("final_response")},
        )
        await self.session.commit()
        return state

    # -----------------------------------------------------------------------
    # SMART ROUTING GRAPH
    # -----------------------------------------------------------------------

    def _build_routing_graph(self, agent_configs: dict[str, Any]):
        graph = StateGraph(WorkflowState)
        graph.add_node("routing_agent", self._make_routing_node(agent_configs))
        graph.add_node("risk_agent", self._make_risk_node(agent_configs))
        graph.add_node("policy_agent", self._make_policy_node(agent_configs))
        graph.set_entry_point("routing_agent")
        graph.add_edge("routing_agent", "risk_agent")
        graph.add_edge("risk_agent", "policy_agent")
        graph.add_edge("policy_agent", END)
        return graph.compile()

    def _make_routing_node(self, agent_configs: dict[str, Any]):
        async def _routing_agent(state: WorkflowState) -> WorkflowState:
            run_id = state["run_id"]
            agent = agent_configs.get("routing_agent")
            system = (
                agent.system_prompt
                if agent
                else "You are a payment routing strategist for Yuno."
            )
            model = agent.model if agent else None
            guardrails = agent.guardrails if agent else []

            transaction_result = lookup_transaction(state["user_message"])
            transaction = transaction_result.output
            country = transaction.get("country", "BR")
            amount = transaction.get("amount", 100.0)
            currency = transaction.get("currency", "BRL")

            health_result = check_provider_health(country)
            fee_result = calculate_fees(country, amount, currency)
            route_result = recommend_route(
                country,
                amount,
                currency,
                health_result.output,
                fee_result.output,
            )

            for result in [transaction_result, health_result, fee_result, route_result]:
                await add_tool_execution(
                    self.session,
                    run_id=run_id,
                    tool_name=result.name,
                    input=result.input,
                    output=result.output,
                    duration_ms=result.duration_ms,
                )

            recommended = route_result.output.get("recommended", {})
            await add_message(
                self.session,
                run_id=run_id,
                sender="Routing Strategy Agent",
                recipient="Risk Conditions Agent",
                channel="agent",
                content=(
                    f"Recommended provider: {recommended.get('provider')} "
                    f"with score {recommended.get('score')} and "
                    f"estimated fee {recommended.get('estimated_fee')}."
                ),
                payload=route_result.output,
            )
            await add_event(
                self.session,
                run_id=run_id,
                event_type="route_scored",
                title="Routing Agent scored all providers",
                body=f"Top provider: {recommended.get('provider')}. Score: {recommended.get('score')}.",
                node_id="routing-agent",
                payload=route_result.output,
            )
            await self.session.commit()

            return {
                **state,
                "transaction": transaction,
                "country": country,
                "amount": amount,
                "currency": currency,
                "provider_health": health_result.output,
                "fee_data": fee_result.output,
                "route_recommendation": route_result.output,
            }

        return _routing_agent

    def _make_risk_node(self, agent_configs: dict[str, Any]):
        async def _risk_agent(state: WorkflowState) -> WorkflowState:
            run_id = state["run_id"]
            agent = agent_configs.get("risk_agent")
            system = (
                agent.system_prompt
                if agent
                else "You are a risk conditions analyst for Yuno."
            )
            model = agent.model if agent else None
            guardrails = agent.guardrails if agent else []

            country = state.get("country", "BR")
            amount = state.get("amount", 100.0)
            risk_result = check_risk_conditions(country, amount)

            await add_tool_execution(
                self.session,
                run_id=run_id,
                tool_name=risk_result.name,
                input=risk_result.input,
                output=risk_result.output,
                duration_ms=risk_result.duration_ms,
            )

            guardrail_note = (
                f" Guardrails: {', '.join(guardrails)}." if guardrails else ""
            )
            llm_result = await self.llm.complete(
                system=system + guardrail_note,
                prompt=(
                    f"Risk conditions for {country}: {risk_result.output}\n"
                    f"Route recommendation: {state.get('route_recommendation')}\n"
                    f"Evaluate risk conditions and flag any issues."
                ),
                fallback=(
                    f"Risk assessment for {country}: "
                    f"3DS required: {risk_result.output.get('three_ds_triggered')}. "
                    f"Chargeback threshold: {risk_result.output.get('chargeback_threshold')}."
                ),
                model=model,
            )

            await add_message(
                self.session,
                run_id=run_id,
                sender="Risk Conditions Agent",
                recipient="Compliance Policy Agent",
                channel="agent",
                content=llm_result.text,
                payload={"risk_conditions": risk_result.output},
            )
            await add_event(
                self.session,
                run_id=run_id,
                event_type="risk_assessed",
                title="Risk Conditions Agent completed assessment",
                body=llm_result.text,
                node_id="risk-agent",
                token_count=llm_result.tokens,
                cost_usd=llm_result.cost_usd,
            )
            await self.session.commit()

            return {
                **state,
                "risk_assessment": risk_result.output,
                "token_count": state.get("token_count", 0) + llm_result.tokens,
                "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + llm_result.cost_usd,
            }

        return _risk_agent

    def _make_policy_node(self, agent_configs: dict[str, Any]):
        async def _policy_agent(state: WorkflowState) -> WorkflowState:
            run_id = state["run_id"]
            agent = agent_configs.get("policy_agent")
            system = (
                agent.system_prompt
                if agent
                else "You are a compliance policy reviewer for Yuno."
            )
            model = agent.model if agent else None
            guardrails = agent.guardrails if agent else []

            recommended = state.get("route_recommendation", {}).get("recommended", {})
            risk_assessment = state.get("risk_assessment", {})

            guardrail_note = (
                f" Guardrails: {', '.join(guardrails)}." if guardrails else ""
            )
            fallback = (
                f"Route approved: {recommended.get('provider')} "
                f"with {recommended.get('success_rate', 0):.1%} success rate "
                f"and estimated fee {recommended.get('estimated_fee')} {state.get('currency', 'BRL')}. "
                f"3DS required: {risk_assessment.get('three_ds_triggered', False)}. "
                f"Fallback: {state.get('route_recommendation', {}).get('fallback', {}).get('provider', 'N/A')}."
            )
            llm_result = await self.llm.complete(
                system=system + guardrail_note,
                prompt=(
                    f"Route recommendation: {state.get('route_recommendation')}\n"
                    f"Risk assessment: {risk_assessment}\n"
                    f"Produce a final compliance-approved routing decision with full reasoning."
                ),
                fallback=fallback,
                model=model,
            )

            await add_message(
                self.session,
                run_id=run_id,
                sender="Compliance Policy Agent",
                recipient="Merchant Ops",
                channel="agent",
                content=llm_result.text,
                payload={"route": state.get("route_recommendation")},
            )
            await add_event(
                self.session,
                run_id=run_id,
                event_type="route_approved",
                title="Policy Agent approved routing decision",
                body=llm_result.text,
                node_id="policy-agent",
                token_count=llm_result.tokens,
                cost_usd=llm_result.cost_usd,
            )
            await self.session.commit()

            return {
                **state,
                "final_response": llm_result.text,
                "confidence": 0.91,
                "needs_approval": False,
                "token_count": state.get("token_count", 0) + llm_result.tokens,
                "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + llm_result.cost_usd,
            }

        return _policy_agent

    # -----------------------------------------------------------------------
    # ROUTING HELPERS
    # -----------------------------------------------------------------------

    @staticmethod
    def _route_after_resolution(
        state: WorkflowState,
    ) -> Literal["approval", "done"]:
        return "approval" if state.get("needs_approval") else "done"


async def execute_workflow_run(
    session: AsyncSession,
    run_id: str,
) -> WorkflowRun:
    runtime = AgentRuntime(session)
    run = await runtime.execute_run(run_id)
    if run.status in {"completed", "failed"} and run.completed_at is None:
        run.completed_at = datetime.now(UTC)
    await session.commit()
    return run