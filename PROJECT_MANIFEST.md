# Project Manifest

This is the runnable MVP implementation, not only an ERD.

### Backend
FastAPI + SQLAlchemy + JWT + RBAC.

### Domain
Customer, InvestmentAccount, RiskAssessment, Portfolio, PortfolioAllocation, PortfolioHolding, PortfolioPerformance, PortfolioDocument, SuitabilityAssessment, PortfolioSubscription, SubscriptionEvent, PortfolioConsent, Transaction, AuditLog.

### APIs
Auth, portfolios, suitability, simulator, subscriptions, consents, dashboard and admin.

### Design intent
The domain boundaries are designed for future Robo-Advisory, Asset Management, managed accounts and fund vehicles without making User the root of the investment model.
