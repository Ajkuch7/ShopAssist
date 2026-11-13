# ShopAssist Architecture

```text
                         +----------------------+
                         | React/Vite frontend  |
                         | customer chat widget |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | FastAPI routes        |
                         | chat/start/health     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | LangGraph state       |
                         | session_id memory     |
                         +----+-------------+----+
                              |             |
                 +------------+             +-------------+
                 v                                        v
       +------------------+                      +------------------+
       | LangChain tools  |                      | ChatOllama       |
       | identity context |                      | local phrasing   |
       +---+----------+---+                      +------------------+
           |          |
           v          v
   +-------------+  +----------------+
   | SQLite      |  | rules.yaml     |
   | synthetic   |  | Python engine  |
   | orders/data |  | money decisions|
   +------+------+  +----------------+
          |
          v
   +----------------+
   | AuditLog and   |
   | action records |
   +----------------+

   policies/*.md + products table
                |
                v
   Ollama embeddings -> Chroma collections
```

## Boundaries

- The browser sends `session_id`, `customer_id`, and free text to FastAPI.
- `SessionContext` supplies customer identity to tools; tools never accept customer IDs as model-selected arguments.
- LangGraph owns the guided step sequence and in-memory session state.
- ChatOllama maps ambiguous language and phrases replies from returned facts. It never decides money.
- `app/rules/rules.yaml` and `app/rules/engine.py` decide eligibility, fees, limits, and refund amounts.
- SQLite stores synthetic customers, orders, refunds, exchanges, escalation cases, and audit logs.
- Chroma provides policy and product retrieval; retrieved records include sources.
- Rotating application logs are written to `logs/shopassist.log`.
