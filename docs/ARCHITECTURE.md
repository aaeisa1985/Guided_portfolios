# Architecture

Customer -> Risk/KYC/AML -> Investment Account -> Suitability -> Consent -> Subscription -> Transaction -> Audit.

The application is intentionally modular:
- `app/main.py`: composition root, middleware, router registration and static frontend.
- `app/models/`: persistence/domain models.
- `app/schemas/`: request/response contracts.
- `app/api/`: domain HTTP routers.
- `app/services/`: reusable domain services.
- `app/core/`: configuration, database and security.

Audit records capture actor, action, entity, source IP and user-agent for sensitive operations.

The current database access remains synchronous SQLAlchemy. This is deliberate: FastAPI supports synchronous route handlers through its worker pool, and the platform is not carrying an async PostgreSQL implementation merely because async drivers exist. A future high-concurrency migration can introduce AsyncSession as a measured performance change rather than architectural debt by assumption.

Production hardening remains: immutable double-entry ledgering, execution/fills, valuation snapshots, real KYC/AML/payment/custody integrations, maker-checker approvals, object storage, observability, rate limiting and jurisdiction-specific controls.
