# Investment Engine Roadmap

Status: foundation-grade, with a production-ready path.

## Completed

- Modular FastAPI composition root and domain routers.
- Customer, account, suitability, consent and subscription foundations.
- Instrument and portfolio-version foundations.
- Idempotency keys and audit metadata.
- Investment orders.
- Execution fills with partial/full fill handling.
- Atomic execution-to-position-to-ledger processing.
- Journal balance validation.
- Realized and unrealized P&L.
- Valuation snapshots.
- CI coverage for core API and execution accounting paths.

## Next before external execution integrations

### 1. Cost-basis lots
Introduce immutable cost lots and a configurable method such as FIFO, average cost or specific identification. The current MVP remains average-cost until the lot engine is implemented and migrated safely.

### 2. Reconciliation
Implement machine-checkable controls for:
- Fill quantity vs position quantity.
- Ledger cash vs operational cash.
- Position valuation vs NAV.
- Accounting-equation control.

### 3. Corporate actions
Model corporate-action events and generated accounting events for splits, dividends, stock dividends, rights issues and mergers.

### 4. FX
Add FX rate, source and timestamp to valuation data and establish a consistent base-currency translation policy.

### 5. Fees
Add management-fee accruals, custody/transaction fees and performance-fee/high-water-mark logic where required by the product.

### 6. Price quality
Track price source and validation status, and reject or flag stale, missing or outlier prices.

### 7. Operational controls
Add maker-checker approval, stronger permission matrices, immutable/reversal-only accounting controls and exception queues.

### 8. External adapters
Only after the internal engine passes reconciliation and failure-mode testing should broker, custodian and payment-provider adapters be connected.


### Selected controls added
The engine now uses explicit average-cost metadata, locks the order/position rows during execution, blocks unpriced open positions from valuation, and exposes account reconciliation checks. These are control improvements without pretending the system has full tax-lot, multi-currency or corporate-action capabilities yet.
