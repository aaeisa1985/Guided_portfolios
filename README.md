# EmCoin Guided Portfolios — Institutional Grade MVP

A complete runnable FastAPI MVP for Guided Portfolios.

## Included
- Customer registration/login with JWT
- Investment accounts
- Risk assessments
- Portfolio catalog and detail API
- Suitability engine
- Projection simulator with scenarios and disclaimer
- Subscription workflow with lifecycle events
- Disclosure consent hashing
- Transactions-ready domain model and audit trail
- Admin seed and audit endpoints
- SQLite zero-config local runtime; Dockerized
- OpenAPI / Swagger

## Run
```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://localhost:8000/docs`.

Seed portfolios: register an account, promote its role to ADMIN in the database, then POST `/api/v1/admin/seed`.

## Architecture
Customer → Risk/KYC/AML → Investment Account → Suitability → Subscription → Portfolio.

Portfolio is deliberately separated from InvestmentAccount so the same core can evolve into Robo-Advisory, Managed Accounts, Asset Management and Funds.

## Production hardening
Replace SQLite with managed PostgreSQL, move secrets to a secrets manager, add real KYC/AML/payment/custody integrations, immutable ledgering, idempotency keys, maker-checker approvals, object storage for documents, notifications, monitoring, rate limiting and UAE-specific regulatory controls before production use.
