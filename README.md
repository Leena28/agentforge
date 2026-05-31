# AgentForge - AI Agent Orchestration Platform
Yuno AI Engineer Challenge Submission by Leena Harpal

##DEMO VIDEO LINK- https://drive.google.com/drive/folders/1pbfkN_ghUqTiVOeqCpnnrnRsSxwXcIAO?usp=drive_link

## PLATFORM IMAGE

<img width="1362" height="678" alt="image" src="https://github.com/user-attachments/assets/3cbf64d1-d4dc-40bb-abb9-51ce15d66c34" />

## What This Is

AgentForge is a production-ready AI Agent Orchestration Platform. Users can create AI agents, configure their behavior, connect them into collaborative workflows, and run them autonomously. Agents communicate asynchronously via LangGraph, all results are persisted in PostgreSQL, and agents are reachable through Slack.

## Runtime Choice - Why LangGraph

LangGraph was chosen over CrewAI, AutoGen, and custom runtimes for these reasons.

LangGraph gives explicit control over the graph topology. Each node is a Python function. Edges can be conditional. Feedback loops are first-class. This matches the payment dispute and routing workflows where the flow must be auditable and deterministic.

CrewAI abstracts too much. The agent-to-agent communication is opaque and harder to wire to a database for persistence.

AutoGen is conversation-first. It works well for chat but not for structured workflows with approval gates and tool calls.

LangGraph state is a typed TypedDict that flows through every node. This makes it straightforward to track tokens, cost, confidence, and inter-agent messages at each step, which the Live Monitor requires.

The runtime reads agent configuration from the database at execution time. system_prompt, model, guardrails, and limits are loaded from the Agent table via runtime_node_binding. This means agent behavior is configurable from the UI without touching code.

## Architecture Decisions

The backend is split into six layers. Channel layer handles Slack and web input. Frontend layer is React with TypeScript and TailwindCSS. Backend layer is FastAPI with Pydantic v2 and SQLAlchemy 2.0. Runtime layer is LangGraph with LiteLLM and Celery. Data layer is PostgreSQL with pgvector and SQLite for tests. Infrastructure layer is Docker and Docker Compose.

SQLAlchemy 2.0 was chosen for full async support with FastAPI. The mapped_column style gives type safety that the older Column syntax does not.

Celery with Redis handles async workflow execution. When a run is triggered via the API or Slack, it is dispatched to a Celery worker so the API returns immediately. Celery Beat reads agent schedules from the database and fires scheduled runs automatically.

pgvector is used for agent memory. Embeddings are stored in PostgreSQL and retrieved via cosine similarity search at runtime. This gives agents persistent memory across runs.

SSE is used for real-time monitoring. The Live Monitor page streams events from the backend as each LangGraph node executes.

SQLite is used in tests so no PostgreSQL instance is required to run the test suite.

## Project Structure
multi_agent_forge/
├── backend/
│   └── app/
│       ├── api/          - FastAPI route handlers
│       ├── channels/     - Slack bot and delivery
│       ├── config/       - Pydantic settings
│       ├── db/           - SQLAlchemy models and session
│       ├── memory/       - pgvector embedding and retrieval
│       ├── runtime/      - LangGraph graphs, LLM client, tools
│       ├── scheduler/    - Celery Beat schedule builder
│       ├── schemas/      - Pydantic request and response schemas
│       ├── services/     - Business logic layer
│       ├── workers/      - Celery task definitions
│       └── seed.py       - Demo data seeding
├── docker/               - Dockerfiles
├── frontend/             - React TypeScript UI
├── tests/                - Pytest test suite
├── docker-compose.yml
└── requirements.txt
## How to Run

### Option 1 - Docker (recommended for evaluation)

Requirements: Docker Desktop installed and running.

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY if you want real LLM responses
# Set ENABLE_LLM=false to run with fallback responses without any API key
docker compose up
```

Open http://localhost:5173 for the UI and http://localhost:8000/docs for the API.

To start the Slack bot (requires Slack credentials in .env):
```bash
docker compose --profile slack up
```

### Option 2 - Local without Docker

Requirements: Python 3.11+, Node.js 20+

```bash
# Backend
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Slack bot (separate terminal, optional)
cd backend
python -m app.channels.slack
```

### Environment Variables

Copy .env.example to .env and configure:

DATABASE_URL=sqlite+aiosqlite:///./agentforge.db  # or PostgreSQL URL
ENABLE_LLM=false                                   # true requires OPENAI_API_KEY
OPENAI_API_KEY=                                    # optional, for real LLM responses
SLACK_BOT_TOKEN=                                   # optional, for Slack integration
SLACK_APP_TOKEN=                                   # optional, for Slack Socket Mode
SLACK_SIGNING_SECRET=                              # optional, for Slack verification
### Running Tests

```bash
cd backend
pytest tests/ -v
```

All 14 tests pass. Tests cover agent creation, workflow execution, and Slack message delivery.

## Two Built-in Workflow Templates

### Yuno Chargeback Management (key: yuno-chargeback-management)

Handles incoming payment chargeback disputes. A message arrives via Slack or the web UI with a transaction ID. The Chargeback Triage Agent classifies the dispute, calls the transaction lookup and fraud risk scoring tools, and passes context to the Resolution Agent. The Resolution Agent drafts a response. If the fraud risk score exceeds 0.50 the workflow pauses at a human approval gate and waits for operator approval before completing.

Agents involved: Chargeback Triage Agent, Resolution Agent.
Tools: transaction_lookup, fraud_risk_scorer.

### Yuno Smart Payment Routing (key: yuno-smart-routing)

Analyses available payment providers to recommend the optimal route for a merchant transaction. The Routing Strategy Agent checks provider health and calculates fees. The Risk Conditions Agent evaluates 3DS requirements and compliance rules. The Compliance Policy Agent produces a final approved routing decision with full reasoning.

Agents involved: Routing Strategy Agent, Risk Conditions Agent, Compliance Policy Agent.
Tools: provider_health_check, fee_calculator, risk_conditions_check, route_recommendation.

## How to Add a New Workflow Template

Step 1 - Define the graph structure in backend/app/seed.py. Add a new dict to BUILTIN_TEMPLATES with key, name, description, category, graph (nodes and edges), and default_input.

Step 2 - Add the LangGraph nodes in backend/app/runtime/langgraph_runtime.py. Create node functions and wire them in a new _build_your_graph method.

Step 3 - Create agent records in DEMO_AGENTS in seed.py with runtime_node_binding set to match your node names.

Step 4 - Restart the server. seed.py runs on startup and upserts the new template automatically.

## How to Add a New Messaging Channel

Step 1 - Create backend/app/channels/your_channel.py. Use slack.py as the reference implementation.

Step 2 - Normalize the inbound message to extract text and metadata. Call create_run with channel set to your channel name and source_metadata containing whatever you need for delivery.

Step 3 - Call execute_workflow_run or execute_workflow_task.delay with the run ID.

Step 4 - Add a delivery function similar to slack_delivery.py that reads run.final_response and posts it back to the channel when the workflow completes.

Step 5 - Register your channel process in docker-compose.yml as a new service.

## Gaps Fixed Beyond the Reference Implementation

The original Codex reference code had four gaps that were identified and fixed:

Gap 1 - Agent config was stored in the database but the runtime ignored it. Fixed by adding runtime_node_binding to the Agent model and loading agent configs via get_agents_by_node_binding at workflow start. Every LangGraph node now reads system_prompt, model, and guardrails from the database.

Gap 2 - Schedules field existed on Agent but nothing triggered scheduled runs. Fixed by building scheduler/beat.py which reads all agent schedules from the database on startup and builds a Celery Beat schedule with crontab entries for daily, hourly, and custom cron modes.

Gap 3 - pgvector was declared in docker-compose but never used. Fixed by implementing memory/pgvector.py with store_memory and retrieve_memory functions using OpenAI embeddings and PostgreSQL cosine similarity search.

Gap 4 - Tests existed for agent creation and workflow execution but not for Slack message delivery. Fixed by adding tests/test_message_delivery.py with four test scenarios covering web channel skip, no token skip, successful delivery, and approval message content.

## Live Demo

The platform was tested end to end with:
- Agent creation via the web UI
- Workflow execution via the Workflow Builder
- Real-time SSE streaming in the Live Monitor
- Human approval gate triggered and approved
- Slack bot receiving a message and triggering a workflow
- Run History showing all runs with channel attribution
