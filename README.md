# EmCoin Guided Portfolios

A production-oriented Guided Portfolios MVP combining an institutional-style web experience with a FastAPI domain backend.

## Product flow

Customer → Authentication → Investor/Risk Profile → Portfolio Shelf → Suitability → Disclosure Consent → Subscription → Lifecycle Events → Dashboard / Activity

## Included

- FastAPI + SQLAlchemy backend
- Customer registration/login with JWT
- Investment account creation
- Risk assessment and suitability engine
- Portfolio catalog, allocations, holdings, NAV performance and documents
- Projection simulator with explicit non-guarantee disclaimer
- Subscription lifecycle and subscription detail
- Recorded disclosure consent with SHA-256 disclosure hash
- Customer activity/audit timeline
- Dashboard metrics
- Responsive institutional frontend
- NAV chart with dates and gridlines
- Animated modals and typed toast notifications
- Docker runtime with persistent SQLite data volume
- OpenAPI / Swagger

## Local run

Copy `.env.example` to `.env`, set a strong `EMCOIN_JWT_SECRET`, then:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

## Docker

```bash
cp .env.example .env
# Set EMCOIN_JWT_SECRET in .env
docker compose up --build
```

The frontend is served by FastAPI at `/`; API documentation is available at `/docs`.

## Seed demo portfolios

Register an account, promote that customer to ADMIN in the database, then POST `/api/v1/admin/seed`.

## Architecture notes

The MVP deliberately keeps the domain model explicit so it can evolve into managed accounts, robo-advisory, asset management and fund workflows.

Current infrastructure uses PostgreSQL + Alembic migrations in Docker. Before production launch, add managed secrets, real KYC/AML, payment/custody integrations, immutable accounting/ledger controls, idempotency enforcement, maker-checker approvals, object storage for documents, notifications, observability, rate limiting and UAE-specific regulatory controls.
