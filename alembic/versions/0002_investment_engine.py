"""Add investment engine and control tables."""
from alembic import op
import sqlalchemy as sa
revision="0002_investment_engine"
down_revision="0001_initial"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    insp=sa.inspect(bind)
    tables=set(insp.get_table_names())
    if "instruments" not in tables:
        op.create_table("instruments",
            sa.Column("id",sa.Uuid(),primary_key=True),
            sa.Column("symbol",sa.String(80),nullable=True),
            sa.Column("name",sa.String(200),nullable=False),
            sa.Column("instrument_type",sa.String(50),nullable=False),
            sa.Column("asset_class",sa.String(80),nullable=False),
            sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),
            sa.Column("isin",sa.String(20),nullable=True),
            sa.Column("status",sa.String(30),nullable=False,server_default="ACTIVE"),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_instruments_symbol","instruments",["symbol"],unique=True)
        op.create_index("ix_instruments_isin","instruments",["isin"],unique=True)
    if "portfolio_versions" not in tables:
        op.create_table("portfolio_versions",
            sa.Column("id",sa.Uuid(),primary_key=True),
            sa.Column("portfolio_id",sa.Uuid(),sa.ForeignKey("portfolios.id"),nullable=False),
            sa.Column("version_number",sa.Integer(),nullable=False),
            sa.Column("status",sa.String(30),nullable=False,server_default="DRAFT"),
            sa.Column("effective_at",sa.DateTime(timezone=True),nullable=True),
            sa.Column("approved_by",sa.Uuid(),nullable=True),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_portfolio_versions_portfolio_id","portfolio_versions",["portfolio_id"])
    if "idempotency_keys" not in tables:
        op.create_table("idempotency_keys",
            sa.Column("id",sa.Uuid(),primary_key=True),
            sa.Column("customer_id",sa.Uuid(),sa.ForeignKey("customers.id"),nullable=False),
            sa.Column("key",sa.String(200),nullable=False),
            sa.Column("endpoint",sa.String(120),nullable=False),
            sa.Column("response_status",sa.Integer(),nullable=False,server_default="200"),
            sa.Column("response_body",sa.Text(),nullable=False),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_idempotency_keys_customer_id","idempotency_keys",["customer_id"])
    if "ledger_entries" not in tables:
        op.create_table("ledger_entries",
            sa.Column("id",sa.Uuid(),primary_key=True),
            sa.Column("account_id",sa.Uuid(),sa.ForeignKey("investment_accounts.id"),nullable=False),
            sa.Column("subscription_id",sa.Uuid(),sa.ForeignKey("portfolio_subscriptions.id"),nullable=True),
            sa.Column("transaction_id",sa.Uuid(),sa.ForeignKey("transactions.id"),nullable=True),
            sa.Column("entry_type",sa.String(40),nullable=False),
            sa.Column("direction",sa.String(10),nullable=False),
            sa.Column("amount",sa.Numeric(18,2),nullable=False),
            sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),
            sa.Column("units",sa.Numeric(18,6),nullable=False,server_default="0"),
            sa.Column("description",sa.Text(),nullable=False,server_default=""),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
        op.create_index("ix_ledger_entries_account_id","ledger_entries",["account_id"])
    cols={x["name"] for x in insp.get_columns("portfolio_holdings")}
    if "instrument_id" not in cols:
        with op.batch_alter_table("portfolio_holdings") as batch:
            batch.add_column(sa.Column("instrument_id",sa.Uuid(),nullable=True))
            batch.create_index("ix_portfolio_holdings_instrument_id",["instrument_id"])
            batch.create_foreign_key("fk_portfolio_holdings_instrument","instruments",["instrument_id"],["id"])
    cols={x["name"] for x in insp.get_columns("portfolio_subscriptions")}
    if "portfolio_version_id" not in cols:
        with op.batch_alter_table("portfolio_subscriptions") as batch:
            batch.add_column(sa.Column("portfolio_version_id",sa.Uuid(),nullable=True))
            batch.create_index("ix_portfolio_subscriptions_portfolio_version_id",["portfolio_version_id"])
            batch.create_foreign_key("fk_portfolio_subscriptions_version","portfolio_versions",["portfolio_version_id"],["id"])

def downgrade():
    with op.batch_alter_table("portfolio_subscriptions") as batch: batch.drop_column("portfolio_version_id")
    with op.batch_alter_table("portfolio_holdings") as batch: batch.drop_column("instrument_id")
    op.drop_table("ledger_entries")
    op.drop_table("idempotency_keys")
    op.drop_table("portfolio_versions")
    op.drop_table("instruments")
