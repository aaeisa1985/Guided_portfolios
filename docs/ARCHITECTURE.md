# Architecture

Customer -> Risk/KYC/AML -> Investment Account -> Suitability -> Consent -> Subscription -> Transaction -> Execution/Fills -> Journalized Ledger -> Position -> Valuation/NAV -> Audit.

The application is intentionally modular:
- `app/main.py`: composition root, middleware, router registration and static frontend.
- `app/models/`: persistence/domain models.
- `app/schemas/`: request/response contracts.
- `app/api/`: domain HTTP routers.
- `app/services/`: reusable domain services.
- `app/core/`: configuration, database and security.

Audit records capture actor, action, entity, source IP and user-agent for sensitive operations.

The current database access remains synchronous SQLAlchemy. This is deliberate: FastAPI supports synchronous route handlers through its worker pool, and the platform is not carrying an async PostgreSQL implementation merely because async drivers exist. A future high-concurrency migration can introduce AsyncSession as a measured performance change rather than architectural debt by assumption.

## Investment engine status

The current engine is **foundation-grade with a production-ready path**. It does not claim to be a live regulated trading platform.

The internal accounting path is:
`Order -> Execution/Fills -> Double-entry Journal -> Position -> Valuation Snapshot`.

Execution updates positions and ledger lines atomically inside one database transaction. Duplicate executions are rejected by execution ID, order overfills are rejected, sells above available quantity are rejected, and journal entries are checked for debit/credit balance.

## Reconciliation controls

The roadmap includes four complementary reconciliation checks:
- Ledger vs cash.
- Executions/fills vs positions.
- Positions vs valuation.
- Accounting equation / balance-sheet control.

## Cost basis

The current position engine uses **average cost** so the existing MVP behavior remains stable. Before tax-lot or jurisdiction-specific reporting is introduced, the model should support an explicit cost-basis method (for example FIFO or specific identification) with immutable tax/inventory lots.

## Planned accounting capabilities

The next investment-engine capabilities are intentionally staged rather than bundled into the execution core:
1. Lot-based cost accounting and configurable cost-basis methodology.
2. Corporate actions: splits, dividends, stock dividends, rights issues, mergers and similar events.
3. Multi-currency valuation with FX rate, source and timestamp captured with valuation data.
4. Fee accruals and performance-fee/high-water-mark processing where applicable.
5. Price-quality controls: stale-price detection, source validation and outlier sanity checks.
6. Reconciliation services and exception reporting.
7. Maker-checker/segregation-of-duties controls for sensitive operational actions.
8. External broker/custodian/payment adapters; these remain separate from the internal accounting engine.

## Operational boundary

No fake broker, custodian or live-market execution is represented by the current MVP. External integrations will enter through explicit adapter interfaces and will generate auditable execution events.

## CI discipline

CI runs for pushes to `main` and pull requests targeting `main`. The workflow uses a concurrency group so superseded runs on the same ref can be cancelled, reducing redundant executions during rapid changes. Future work should be batched into a small number of coherent commits before validation to avoid unnecessary CI churn.
