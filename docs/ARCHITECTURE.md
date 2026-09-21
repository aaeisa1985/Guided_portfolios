# Architecture

Customer -> Risk/KYC/AML -> Investment Account -> Suitability -> Consent -> Subscription -> Transaction -> Audit.

Portfolio, investor account, risk and transaction domains are separated conceptually so the MVP can evolve into Robo-Advisory, Managed Accounts, Asset Management and Funds.

Production hardening: immutable ledgering, idempotency keys, maker-checker approvals, object storage, real KYC/AML/payment/custody integrations, observability and jurisdiction-specific controls.