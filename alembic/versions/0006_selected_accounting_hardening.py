"""Selected accounting hardening."""
from alembic import op
import sqlalchemy as sa
revision="0006_selected_accounting_hardening"
down_revision="0005_execution_accounting"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); inspector=sa.inspect(bind); tables=set(inspector.get_table_names())
    if "portfolios" in tables and "cost_basis_method" not in {c["name"] for c in inspector.get_columns("portfolios")}:
        with op.batch_alter_table("portfolios") as batch:
            batch.add_column(sa.Column("cost_basis_method",sa.String(30),nullable=False,server_default="AVERAGE_COST"))
    if "portfolio_positions" in tables:
        cols={c["name"] for c in inspector.get_columns("portfolio_positions")}
        with op.batch_alter_table("portfolio_positions") as batch:
            if "realized_pnl" not in cols: batch.add_column(sa.Column("realized_pnl",sa.Numeric(18,2),nullable=False,server_default="0"))
            if "price_as_of" not in cols: batch.add_column(sa.Column("price_as_of",sa.DateTime(timezone=True),nullable=True))
            if "price_source" not in cols: batch.add_column(sa.Column("price_source",sa.String(120),nullable=False,server_default="INTERNAL"))
        if "uq_portfolio_position_key" not in {i["name"] for i in inspector.get_indexes("portfolio_positions")}:
            op.create_index("uq_portfolio_position_key","portfolio_positions",["account_id","portfolio_id","instrument_id"],unique=True)

def downgrade():
    bind=op.get_bind(); inspector=sa.inspect(bind); tables=set(inspector.get_table_names())
    if "portfolio_positions" in tables:
        if "uq_portfolio_position_key" in {i["name"] for i in inspector.get_indexes("portfolio_positions")}:
            op.drop_index("uq_portfolio_position_key",table_name="portfolio_positions")
        cols={c["name"] for c in inspector.get_columns("portfolio_positions")}
        with op.batch_alter_table("portfolio_positions") as batch:
            if "price_source" in cols: batch.drop_column("price_source")
            if "price_as_of" in cols: batch.drop_column("price_as_of")
            if "realized_pnl" in cols: batch.drop_column("realized_pnl")
    if "portfolios" in tables and "cost_basis_method" in {c["name"] for c in inspector.get_columns("portfolios")}:
        with op.batch_alter_table("portfolios") as batch: batch.drop_column("cost_basis_method")
