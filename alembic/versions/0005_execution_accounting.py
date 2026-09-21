"""Execution fills, journalized ledgering and valuation snapshots."""
from alembic import op
import sqlalchemy as sa

revision="0005_execution_accounting"
down_revision="0004_audit_and_idempotency"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    tables=set(inspector.get_table_names())
    if "ledger_journals" not in tables:
        op.create_table("ledger_journals",
            sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("account_id",sa.Uuid(),sa.ForeignKey("investment_accounts.id"),nullable=False),
            sa.Column("reference_type",sa.String(50),nullable=False),sa.Column("reference_id",sa.Uuid(),nullable=True),
            sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),sa.Column("description",sa.Text(),nullable=False,server_default=""),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_ledger_journals_account_id","ledger_journals",["account_id"])
        op.create_index("ix_ledger_journals_reference_id","ledger_journals",["reference_id"])
    if "execution_fills" not in tables:
        op.create_table("execution_fills",
            sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("order_id",sa.Uuid(),sa.ForeignKey("investment_orders.id"),nullable=False),
            sa.Column("execution_id",sa.String(200),nullable=False),sa.Column("quantity",sa.Numeric(24,8),nullable=False),
            sa.Column("price",sa.Numeric(24,8),nullable=False),sa.Column("fees",sa.Numeric(18,2),nullable=False,server_default="0"),
            sa.Column("executed_at",sa.DateTime(timezone=True),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_execution_fills_order_id","execution_fills",["order_id"])
        op.create_index("uq_execution_fill_execution_id","execution_fills",["execution_id"],unique=True)
    if "valuation_snapshots" not in tables:
        op.create_table("valuation_snapshots",
            sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("account_id",sa.Uuid(),sa.ForeignKey("investment_accounts.id"),nullable=False),
            sa.Column("portfolio_id",sa.Uuid(),sa.ForeignKey("portfolios.id"),nullable=True),sa.Column("as_of",sa.DateTime(timezone=True),nullable=False),
            sa.Column("cash_value",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("market_value",sa.Numeric(18,2),nullable=False,server_default="0"),
            sa.Column("nav",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),
            sa.Column("price_source",sa.String(120),nullable=False,server_default="INTERNAL"))
        op.create_index("ix_valuation_snapshots_account_id","valuation_snapshots",["account_id"])
        op.create_index("ix_valuation_snapshots_portfolio_id","valuation_snapshots",["portfolio_id"])
        op.create_index("ix_valuation_snapshots_as_of","valuation_snapshots",["as_of"])
    if "ledger_entries" in tables:
        cols={c["name"] for c in inspector.get_columns("ledger_entries")}
        if "journal_id" not in cols or "ledger_account" not in cols:
            with op.batch_alter_table("ledger_entries") as batch:
                if "journal_id" not in cols: batch.add_column(sa.Column("journal_id",sa.Uuid(),sa.ForeignKey("ledger_journals.id"),nullable=True))
                if "ledger_account" not in cols: batch.add_column(sa.Column("ledger_account",sa.String(80),nullable=True))
    if "portfolio_positions" in tables and "realized_pnl" not in {c["name"] for c in inspector.get_columns("portfolio_positions")}:
        with op.batch_alter_table("portfolio_positions") as batch: batch.add_column(sa.Column("realized_pnl",sa.Numeric(18,2),nullable=False,server_default="0"))

def downgrade():
    bind=op.get_bind(); inspector=sa.inspect(bind); tables=set(inspector.get_table_names())
    if "portfolio_positions" in tables and "realized_pnl" in {c["name"] for c in inspector.get_columns("portfolio_positions")}:
        with op.batch_alter_table("portfolio_positions") as batch: batch.drop_column("realized_pnl")
    if "ledger_entries" in tables:
        cols={c["name"] for c in inspector.get_columns("ledger_entries")}
        with op.batch_alter_table("ledger_entries") as batch:
            if "ledger_account" in cols: batch.drop_column("ledger_account")
            if "journal_id" in cols: batch.drop_column("journal_id")
    if "valuation_snapshots" in tables: op.drop_table("valuation_snapshots")
    if "execution_fills" in tables: op.drop_table("execution_fills")
    if "ledger_journals" in tables: op.drop_table("ledger_journals")
