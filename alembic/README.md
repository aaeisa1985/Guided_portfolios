# Alembic

Alembic is the migration surface for the Guided Portfolios platform.

Docker runs `alembic upgrade head` before starting the API. The migration environment loads metadata from `app.models`.

The current migration chain preserves compatibility with the existing MVP database while adding the investment engine, positions/orders, audit metadata and idempotency constraints.
