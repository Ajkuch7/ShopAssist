# ShopAssist

ShopAssist is a small synthetic e-commerce customer-care chatbot. It proves an agent can guide a customer through returns, refunds, exchanges, and buying a different product without connecting to a real store.

The LLM understands free text and phrases replies. LangGraph controls the conversation steps. Python rules and SQLite data decide eligibility, fees, refunds, and amounts.

## Architecture

```text
React/Vite UI (frontend/) + chat CLI
                 |
                 v
          FastAPI API (app/api)
                 |
                 v
       LangGraph state machine (app/agent)
          /          |            \
         v           v             v
   LangChain tools  RAG          Guardrails
         |        Chroma          |
         v           |             v
   SQLite queries <--+------> Ollama
         |
         v
  Synthetic orders, products, audit logs

rules.yaml --> pure Python eligibility and fee engine
policies/*.md --> Chroma policy collection
products table --> Chroma product collection
```

## Setup

Requirements: Python 3.12, Node.js/npm, Git, and Ollama.

```powershell
cd "D:\AIML project\shopassist"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

The frontend reads `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Pull the configured local models:

```powershell
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

Generate the synthetic SQLite data:

```powershell
.\.venv\Scripts\python.exe -m app.db.seed
```

## Run

Start the API and React UI together:

```powershell
.\run_all.ps1
```

Or start them separately:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
cd frontend
npm run dev
```

The API is at `http://localhost:8000`, the UI is at `http://localhost:5173`, and health is at `http://localhost:8000/health`.

Logs are written to `logs/shopassist.log`.

## Demo

Follow the ten-step walkthrough in [docs/DEMO.md](docs/DEMO.md). The interactive CLI is also available:

```powershell
.\.venv\Scripts\python.exe scripts/chat_cli.py --customer 1
```

## Tests and Evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest tests\test_scenarios.py -v
.\.venv\Scripts\python.exe scripts/evaluate.py --model qwen2.5:7b
.\.venv\Scripts\python.exe -m app.rag.ingest
.\.venv\Scripts\python.exe scripts/rag_test.py "What is the return window for clothing?"
```

The evaluator writes model metrics to `results/model_comparison.md`. RAG ingestion requires Ollama with `nomic-embed-text` available.

## Folder Tree

```text
shopassist/
|-- app/
|   |-- agent/          LangGraph state machine and guardrails
|   |-- api/            FastAPI routes and schemas
|   |-- core/           Settings, Ollama client, logging
|   |-- db/             SQLAlchemy models, queries, seed data
|   |-- rag/            Chroma ingestion and retrieval
|   |-- rules/          YAML rules loader and pure Python engine
|   `-- tools/          Context-bound LangChain tools
|-- data/
|   |-- policies/      Synthetic policy documents
|   `-- products.csv
|-- docs/
|   |-- ARCHITECTURE.md
|   `-- DEMO.md
|-- frontend/           React/Vite storefront and chat widget
|-- scripts/            CLI, evaluation, ingestion helpers
|-- tests/              Rules, tools, flow, and scenario tests
|-- config.yaml
|-- requirements.txt
|-- run_all.ps1
`-- Dockerfile
```

## Runtime Errors

The API returns a friendly `503` when Ollama is down, the configured model is missing, or the synthetic database is empty. The response includes the corrective command where possible, and dependency status is visible at `/health`.
