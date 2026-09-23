"""Enable RLS on all application tables in the exposed public schema.
Revision ID: 0009_enable_rls
Revises: 0008_manager_governance
"""
from alembic import op

revision = "0009_enable_rls"
down_revision = "0008_manager_governance"
branch_labels = None
depends_on = None

_TABLES = [
    "audit_logs",
    "corporate_action_events",
    "corporate_actions",
    "customers",
    "execution_fills",
    "idempotency_keys",
    "instruments",
    "investment_accounts",
    "investment_orders",
    "ledger_entries",
    "ledger_journals",
    "portfolio_allocations",
    "portfolio_consents",
    "portfolio_documents",
    "portfolio_holdings",
    "portfolio_performance",
    "portfolio_positions",
    "portfolio_subscriptions",
    "portfolio_versions",
    "portfolios",
    "risk_assessments",
    "subscription_events",
    "suitability_assessments",
    "transactions",
    "valuation_snapshots",
]


def upgrade():
    for table in _TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade():
    for table in _TABLES:
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
