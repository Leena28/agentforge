import re
import time
from dataclasses import dataclass
from typing import Any


TRANSACTIONS = {
    "TXN-4821": {
        "transaction_id": "TXN-4821",
        "merchant_id": "M-RAPPI-BR",
        "merchant_name": "Rappi Brazil",
        "country": "BR",
        "currency": "BRL",
        "amount": 350.0,
        "provider": "Adyen",
        "status": "captured",
        "payment_method": "credit_card",
        "customer_id": "C-88821",
        "events": [
            "auth_approved",
            "capture_approved",
            "chargeback_received",
        ],
        "customer_history": {
            "prior_chargebacks": 0,
            "successful_payments": 12,
            "account_age_days": 420,
        },
        "chargeback_reason_code": "4853",
        "chargeback_reason": "cardholder_dispute",
    },
    "TXN-9034": {
        "transaction_id": "TXN-9034",
        "merchant_id": "M-IFOOD-BR",
        "merchant_name": "iFood Brazil",
        "country": "BR",
        "currency": "BRL",
        "amount": 420.0,
        "provider": "Stripe",
        "status": "captured",
        "payment_method": "credit_card",
        "customer_id": "C-77234",
        "events": [
            "auth_approved",
            "capture_approved",
            "chargeback_received",
            "duplicate_auth_detected",
        ],
        "customer_history": {
            "prior_chargebacks": 2,
            "successful_payments": 8,
            "account_age_days": 90,
        },
        "chargeback_reason_code": "4840",
        "chargeback_reason": "fraudulent_transaction",
    },
    "TXN-6612": {
        "transaction_id": "TXN-6612",
        "merchant_id": "M-MERCADO-MX",
        "merchant_name": "Mercado Libre Mexico",
        "country": "MX",
        "currency": "MXN",
        "amount": 1200.0,
        "provider": "Conekta",
        "status": "captured",
        "payment_method": "debit_card",
        "customer_id": "C-55109",
        "events": [
            "auth_approved",
            "capture_approved",
            "chargeback_received",
        ],
        "customer_history": {
            "prior_chargebacks": 1,
            "successful_payments": 25,
            "account_age_days": 730,
        },
        "chargeback_reason_code": "4853",
        "chargeback_reason": "cardholder_dispute",
    },
}

PROVIDER_HEALTH = {
    "Adyen": {
        "provider": "Adyen",
        "success_rate": 0.971,
        "latency_ms": 380,
        "incident": None,
        "supported_countries": ["BR", "MX", "CO", "AR", "CL"],
        "supported_currencies": ["BRL", "MXN", "COP", "ARS", "CLP"],
    },
    "Stripe": {
        "provider": "Stripe",
        "success_rate": 0.958,
        "latency_ms": 420,
        "incident": "latency_degradation",
        "supported_countries": ["BR", "MX", "CO"],
        "supported_currencies": ["BRL", "MXN", "COP"],
    },
    "Conekta": {
        "provider": "Conekta",
        "success_rate": 0.943,
        "latency_ms": 510,
        "incident": None,
        "supported_countries": ["MX"],
        "supported_currencies": ["MXN"],
    },
    "Kushki": {
        "provider": "Kushki",
        "success_rate": 0.962,
        "latency_ms": 440,
        "incident": None,
        "supported_countries": ["CO", "EC", "PE"],
        "supported_currencies": ["COP", "USD", "PEN"],
    },
    "Mercado Pago": {
        "provider": "Mercado Pago",
        "success_rate": 0.934,
        "latency_ms": 590,
        "incident": None,
        "supported_countries": ["BR", "MX", "AR", "CO", "CL"],
        "supported_currencies": ["BRL", "MXN", "ARS", "COP", "CLP"],
    },
}

PROVIDER_FEES = {
    "Adyen": {
        "fee_percent": 2.2,
        "fx_spread_percent": 0.5,
        "min_fee_usd": 0.10,
    },
    "Stripe": {
        "fee_percent": 2.9,
        "fx_spread_percent": 0.4,
        "min_fee_usd": 0.30,
    },
    "Conekta": {
        "fee_percent": 2.4,
        "fx_spread_percent": 0.8,
        "min_fee_usd": 0.15,
    },
    "Kushki": {
        "fee_percent": 2.1,
        "fx_spread_percent": 0.6,
        "min_fee_usd": 0.10,
    },
    "Mercado Pago": {
        "fee_percent": 3.2,
        "fx_spread_percent": 0.9,
        "min_fee_usd": 0.20,
    },
}

RISK_CONDITIONS = {
    "BR": {
        "requires_3ds": True,
        "max_amount_no_3ds": 500.0,
        "currency": "BRL",
        "high_risk_mccs": ["7995", "6211"],
        "chargeback_threshold": 0.01,
    },
    "MX": {
        "requires_3ds": False,
        "max_amount_no_3ds": 2000.0,
        "currency": "MXN",
        "high_risk_mccs": ["7995"],
        "chargeback_threshold": 0.015,
    },
    "CO": {
        "requires_3ds": True,
        "max_amount_no_3ds": 300.0,
        "currency": "COP",
        "high_risk_mccs": ["7995", "6211", "5912"],
        "chargeback_threshold": 0.012,
    },
}

@dataclass(slots=True)
class ToolResult:
    name: str
    input: dict[str, Any]
    output: dict[str, Any]
    duration_ms: int


def _measure(name: str, payload: dict[str, Any], fn: Any) -> ToolResult:
    started = time.perf_counter()
    output = fn()
    duration_ms = int((time.perf_counter() - started) * 1000)
    return ToolResult(name=name, input=payload, output=output, duration_ms=duration_ms)


def extract_transaction_id(message: str) -> str:
    match = re.search(r"TXN-\d{4}", message.upper())
    return match.group(0) if match else "TXN-4821"


def lookup_transaction(message: str) -> ToolResult:
    transaction_id = extract_transaction_id(message)

    def run() -> dict[str, Any]:
        return TRANSACTIONS.get(transaction_id, TRANSACTIONS["TXN-4821"])

    return _measure(
        "transaction_lookup",
        {"message": message, "transaction_id": transaction_id},
        run,
    )


def score_fraud_risk(
    transaction: dict[str, Any],
    provider_health: dict[str, Any],
) -> ToolResult:
    def run() -> dict[str, Any]:
        duplicate_signal = "duplicate_auth_detected" in transaction.get("events", [])
        incident_signal = bool(provider_health.get("incident"))
        prior_chargebacks = transaction.get("customer_history", {}).get(
            "prior_chargebacks", 0
        )
        account_age = transaction.get("customer_history", {}).get(
            "account_age_days", 365
        )
        reason_code = transaction.get("chargeback_reason_code", "")

        score = 0.15
        if duplicate_signal:
            score += 0.30
        if incident_signal:
            score += 0.15
        if prior_chargebacks > 0:
            score += min(prior_chargebacks * 0.10, 0.25)
        if account_age < 180:
            score += 0.10
        if reason_code == "4840":
            score += 0.20

        score = min(score, 0.97)
        confidence = 0.88 if duplicate_signal else 0.74
        reason = (
            "fraudulent_transaction"
            if reason_code == "4840"
            else "cardholder_dispute"
        )

        return {
            "score": round(score, 2),
            "confidence": confidence,
            "reason": reason,
            "duplicate_signal": duplicate_signal,
            "prior_chargebacks": prior_chargebacks,
            "requires_human_approval": score >= 0.50,
        }

    return _measure(
        "fraud_risk_scorer",
        {"transaction": transaction, "provider_health": provider_health},
        run,
    )


def draft_chargeback_response(
    transaction: dict[str, Any],
    fraud_risk: dict[str, Any],
) -> str:
    if fraud_risk["requires_human_approval"]:
        return (
            f"Chargeback dispute for transaction {transaction['transaction_id']} "
            f"from {transaction['merchant_name']} requires human approval. "
            f"Fraud risk score: {fraud_risk['score']} "
            f"(confidence: {fraud_risk['confidence']}). "
            f"Reason: {fraud_risk['reason']}. "
            "Draft response has been prepared and is pending operator approval "
            "before being sent to the acquiring bank."
        )
    return (
        f"Transaction {transaction['transaction_id']} from "
        f"{transaction['merchant_name']} shows low fraud risk "
        f"(score: {fraud_risk['score']}). "
        "Recommend standard chargeback representment process. "
        "No immediate escalation required."
    )


# ---------------------------------------------------------------------------
# SMART ROUTING TOOLS
# ---------------------------------------------------------------------------

def check_provider_health(country: str) -> ToolResult:
    def run() -> dict[str, Any]:
        available = {
            name: health
            for name, health in PROVIDER_HEALTH.items()
            if country in health["supported_countries"]
        }
        return available

    return _measure(
        "provider_health_check",
        {"country": country},
        run,
    )


def calculate_fees(
    country: str,
    amount: float,
    currency: str,
) -> ToolResult:
    def run() -> dict[str, Any]:
        results = {}
        for provider, fees in PROVIDER_FEES.items():
            health = PROVIDER_HEALTH.get(provider, {})
            if country not in health.get("supported_countries", []):
                continue
            total_fee_percent = fees["fee_percent"] + fees["fx_spread_percent"]
            estimated_fee = max(
                amount * (total_fee_percent / 100),
                fees["min_fee_usd"],
            )
            results[provider] = {
                "fee_percent": fees["fee_percent"],
                "fx_spread_percent": fees["fx_spread_percent"],
                "total_fee_percent": round(total_fee_percent, 2),
                "estimated_fee": round(estimated_fee, 2),
                "currency": currency,
            }
        return results

    return _measure(
        "fee_calculator",
        {"country": country, "amount": amount, "currency": currency},
        run,
    )


def check_risk_conditions(
    country: str,
    amount: float,
) -> ToolResult:
    def run() -> dict[str, Any]:
        conditions = RISK_CONDITIONS.get(country, {})
        requires_3ds = conditions.get("requires_3ds", False)
        max_no_3ds = conditions.get("max_amount_no_3ds", 1000.0)
        three_ds_required = requires_3ds and amount > max_no_3ds
        return {
            "country": country,
            "amount": amount,
            "requires_3ds": requires_3ds,
            "three_ds_triggered": three_ds_required,
            "chargeback_threshold": conditions.get("chargeback_threshold", 0.01),
            "high_risk_mccs": conditions.get("high_risk_mccs", []),
        }

    return _measure(
        "risk_conditions_check",
        {"country": country, "amount": amount},
        run,
    )


def recommend_route(
    country: str,
    amount: float,
    currency: str,
    provider_health: dict[str, Any],
    fee_data: dict[str, Any],
) -> ToolResult:
    def run() -> dict[str, Any]:
        candidates = []
        for provider, health in provider_health.items():
            if health.get("incident") == "critical_outage":
                continue
            fees = fee_data.get(provider, {})
            estimated_fee = fees.get("estimated_fee", 0)
            success_rate = health.get("success_rate", 0)
            health_penalty = (1 - success_rate) * 20
            incident_penalty = 5 if health.get("incident") else 0
            score = round(
                (success_rate * 100) - estimated_fee - health_penalty - incident_penalty,
                2,
            )
            candidates.append({
                "provider": provider,
                "score": score,
                "success_rate": success_rate,
                "estimated_fee": estimated_fee,
                "latency_ms": health.get("latency_ms", 0),
                "incident": health.get("incident"),
            })
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return {
            "recommended": candidates[0] if candidates else {},
            "fallback": candidates[1] if len(candidates) > 1 else {},
            "all_candidates": candidates,
        }

    return _measure(
        "route_recommendation",
        {
            "country": country,
            "amount": amount,
            "currency": currency,
        },
        run,
    )