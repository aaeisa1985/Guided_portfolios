"""Audit metadata and idempotency uniqueness."""
from alembic import op
import sqlalchemy as sa

revision="0004_audit_and_idempotency"
down_revision="0003_positions_orders"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if "audit_logs" in inspector.get_table_names():
        cols={c["name"] for c in inspector.get_columns("audit_logs")}
        if "user_agent" not in cols:
            with op.batch_alter_table("audit_logs") as batch:
                batch.add_column(sa.Column("user_agent",sa.String(length=512),nullable=True))
    if "idempotency_keys" in inspector.get_table_names():
        indexes={i["name"] for i in inspector.get_indexes("idempotency_keys")}
        constraints={i["name"] for i in inspector.get_unique_constraints("idempotency_keys")}
        if "uq_idempotency_customer_key_endpoint" not in indexes and "uq_idempotency_customer_key_endpoint" not in constraints:
            op.create_index("uq_idempotency_customer_key_endpoint","idempotency_keys",["customer_id","key","endpoint"],unique=True)
    if "investment_orders" in inspector.get_table_names():
        indexes={i["name"] for i in inspector.get_indexes("investment_orders")}
        constraints={i["name"] for i in inspector.get_unique_constraints("investment_orders")}
        if "uq_investment_order_idempotency_key" not in indexes and "uq_investment_order_idempotency_key" not in constraints:
            op.create_index("uq_investment_order_idempotency_key","investment_orders",["idempotency_key"],unique=True)

def downgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if "investment_orders" in inspector.get_table_names():
        if any(i["name"]=="uq_investment_order_idempotency_key" for i in inspector.get_indexes("investment_orders")):
            op.drop_index("uq_investment_order_idempotency_key",table_name="investment_orders")
    if "idempotency_keys" in inspector.get_table_names():
        if any(i["name"]=="uq_idempotency_customer_key_endpoint" for i in inspector.get_indexes("idempotency_keys")):
            op.drop_index("uq_idempotency_customer_key_endpoint",table_name="idempotency_keys")
    if "audit_logs" in inspector.get_table_names() and "user_agent" in {c["name"] for c in inspector.get_columns("audit_logs")}:
        with op.batch_alter_table("audit_logs") as batch:
            batch.drop_column("user_agent")
