# Architecture

```
+--------------------------+           +------------------+
|        Frontend/UI       |<--------->| FastAPI Backend  |
|  (minimal HTML or API)   |           |  Auth + API      |
+--------------------------+           +------------------+
                                              |
                                              v
                                        +-----------+
                                        | Postgres  |
                                        +-----------+
                                              |
                                              v
                                        +-----------+
                                        |  Redis    |
                                        +-----------+
```

Data flow:
1. User registers and logs in.
2. Company created under org.
3. Actuals uploaded via CSV and stored as canonical records.
4. KPI engine computes metrics; forecast + scenarios executed.
5. Excel pack generated on-demand.
6. Portfolio dashboard aggregates risk flags.

Observability:
- Structured logs
- OpenTelemetry hooks
- /health endpoint
