# ShopAssist Demo

1. Start Ollama and make sure `qwen2.5:7b` is installed:
   `ollama pull qwen2.5:7b`.
2. Generate the synthetic SQLite data:
   `\.venv\Scripts\python.exe -m app.db.seed`.
3. Start both services with `\.\run_all.ps1`.
4. Open `http://localhost:5173` and click **Need a hand?**.
5. Choose a demo customer and select the delivered electronics order.
6. Say `The item is defective` and choose **Refund**.
7. Choose **Original payment** and confirm the refund ID and `3-5 business days` timeline.
8. Click **New chat**, select the same order, report `damaged`, choose **Exchange**, then choose **UPS drop-off**.
9. Expand **Agent activity** to show the eligibility, return-method, and exchange tool calls.
10. Open a final new chat, ask a policy question, or say `no, nothing else` to see the closing state.

Useful checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
.\.venv\Scripts\python.exe -m pytest -q
```

Expected health output has `status: ok`, `ollama: ok`, and `database: ok`. If a dependency is missing, the API returns a friendly message and writes details to `logs/shopassist.log`.
