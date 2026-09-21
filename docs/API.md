# API

## Health
GET /health
GET /health/ready

## Customer
POST /api/v1/auth/register
POST /api/v1/auth/login
GET /api/v1/auth/me
GET /api/v1/portfolios
GET /api/v1/portfolios/{id}
POST /api/v1/suitability/check
POST /api/v1/simulator
POST /api/v1/subscriptions
GET /api/v1/subscriptions
GET /api/v1/subscriptions/{id}
POST /api/v1/consents
GET /api/v1/dashboard
GET /api/v1/positions
GET /api/v1/activity

## Staff / Admin
POST /api/v1/admin/seed
GET /api/v1/admin/audit
POST /api/v1/admin/instruments
GET /api/v1/admin/instruments
POST /api/v1/admin/portfolios/{id}/versions
POST /api/v1/admin/portfolios/{id}/versions/{version_id}/approve
POST /api/v1/admin/orders
POST /api/v1/admin/orders/{order_id}/cancel
POST /api/v1/admin/ledger
GET /api/v1/admin/ledger/{account_id}

Sensitive write operations should carry an `X-Request-ID` when clients need correlation and `X-Idempotency-Key` for supported idempotent commands.
