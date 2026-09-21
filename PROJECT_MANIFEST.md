# EmCoin MVP Project Manifest

Institutional-grade foundation: PostgreSQL schema, SQLAlchemy 2 async ORM, Alembic migrations, FastAPI REST/OpenAPI, JWT authentication + RBAC, suitability service, portfolio simulator, subscription lifecycle + events, consents, audit log, dashboard, Dockerized local stack and health test.

Entities: Customer, InvestmentAccount, RiskAssessment, Portfolio, PortfolioAllocation, PortfolioHolding, PortfolioPerformance, PortfolioDocument, SuitabilityAssessment, PortfolioSubscription, PortfolioConsent, Transaction, SubscriptionEvent, AuditLog.

Customer, InvestmentAccount and Portfolio are deliberately separated for future Robo-Advisory, managed accounts, Asset Management and Funds.
