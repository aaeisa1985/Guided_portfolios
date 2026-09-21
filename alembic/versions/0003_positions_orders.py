"""Add positions and order lifecycle."""
from alembic import op
import sqlalchemy as sa
revision="0003_positions_orders"
down_revision="0002_investment_engine"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("portfolio_positions",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("account_id",sa.Uuid(),sa.ForeignKey("investment_accounts.id"),nullable=False),
        sa.Column("portfolio_id",sa.Uuid(),sa.ForeignKey("portfolios.id"),nullable=False),
        sa.Column("instrument_id",sa.Uuid(),sa.ForeignKey("instruments.id"),nullable=False),
        sa.Column("quantity",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("average_cost",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("market_price",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    for n,c in [("account_id","account_id"),("portfolio_id","portfolio_id"),("instrument_id","instrument_id")]:
        op.create_index("ix_portfolio_positions_"+n,"portfolio_positions",[c])
    op.create_table("investment_orders",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("account_id",sa.Uuid(),sa.ForeignKey("investment_accounts.id"),nullable=False),
        sa.Column("portfolio_id",sa.Uuid(),sa.ForeignKey("portfolios.id"),nullable=False),
        sa.Column("instrument_id",sa.Uuid(),sa.ForeignKey("instruments.id"),nullable=False),
        sa.Column("side",sa.String(10),nullable=False),
        sa.Column("order_type",sa.String(20),nullable=False,server_default="MARKET"),
        sa.Column("quantity",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("limit_price",sa.Numeric(24,8),nullable=True),
        sa.Column("status",sa.String(30),nullable=False,server_default="PENDING"),
        sa.Column("idempotency_key",sa.String(200),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    for n in ["account_id","portfolio_id","instrument_id","idempotency_key"]:
        op.create_index("ix_investment_orders_"+n,"investment_orders",[n])

def downgrade():
    op.drop_table("investment_orders")
    op.drop_table("portfolio_positions")
