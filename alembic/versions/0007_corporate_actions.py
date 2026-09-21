"""Corporate actions engine.
Revision ID: 0007_corporate_actions
Revises: 0006_selected_accounting_hardening
"""
from alembic import op
import sqlalchemy as sa
revision="0007_corporate_actions"
down_revision="0006_selected_accounting_hardening"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("corporate_actions",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("instrument_id",sa.Uuid(),sa.ForeignKey("instruments.id"),nullable=False),
        sa.Column("action_type",sa.String(30),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="DRAFT"),
        sa.Column("ex_date",sa.DateTime(timezone=True),nullable=False),sa.Column("record_date",sa.DateTime(timezone=True)),
        sa.Column("payment_date",sa.DateTime(timezone=True)),sa.Column("effective_date",sa.DateTime(timezone=True),nullable=False),
        sa.Column("ratio_numerator",sa.Numeric(18,8)),sa.Column("ratio_denominator",sa.Numeric(18,8)),sa.Column("dividend_per_share",sa.Numeric(24,8)),
        sa.Column("subscription_price",sa.Numeric(24,8)),sa.Column("currency",sa.String(3),nullable=False,server_default="AED"),
        sa.Column("replacement_instrument_id",sa.Uuid(),sa.ForeignKey("instruments.id")),sa.Column("exchange_ratio",sa.Numeric(18,8)),
        sa.Column("description",sa.Text(),nullable=False,server_default=""),sa.Column("failure_reason",sa.Text()),
        sa.Column("approved_by",sa.Uuid(),sa.ForeignKey("customers.id")),sa.Column("approved_at",sa.DateTime(timezone=True)),
        sa.Column("executed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("created_by",sa.Uuid(),sa.ForeignKey("customers.id"),nullable=False),
        sa.UniqueConstraint("instrument_id","action_type","ex_date",name="uq_corporate_action_key"),
        sa.CheckConstraint("action_type IN ('SPLIT','REVERSE_SPLIT','CASH_DIVIDEND','STOCK_DIVIDEND','RIGHTS_ISSUE','MERGER')",name="ck_corporate_action_type"))
    op.create_index("ix_corporate_actions_instrument_id","corporate_actions",["instrument_id"])
    op.create_index("ix_corporate_actions_ex_date","corporate_actions",["ex_date"])
    op.create_index("ix_corporate_actions_status","corporate_actions",["status"])
    op.create_table("corporate_action_events",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("corporate_action_id",sa.Uuid(),sa.ForeignKey("corporate_actions.id"),nullable=False),
        sa.Column("position_id",sa.Uuid(),sa.ForeignKey("portfolio_positions.id"),nullable=False),sa.Column("journal_id",sa.Uuid(),sa.ForeignKey("ledger_journals.id")),
        sa.Column("quantity_before",sa.Numeric(24,8),nullable=False),sa.Column("quantity_after",sa.Numeric(24,8),nullable=False),
        sa.Column("price_before",sa.Numeric(24,8),nullable=False),sa.Column("price_after",sa.Numeric(24,8),nullable=False),
        sa.Column("average_cost_before",sa.Numeric(24,8),nullable=False),sa.Column("average_cost_after",sa.Numeric(24,8),nullable=False),
        sa.Column("cash_impact",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("income_recognized",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("fractional_units",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("cash_in_lieu",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("corporate_action_id","position_id",name="uq_corporate_action_event_key"))
    op.create_index("ix_corporate_action_events_corporate_action_id","corporate_action_events",["corporate_action_id"])
    op.create_index("ix_corporate_action_events_position_id","corporate_action_events",["position_id"])
def downgrade():
    op.drop_table("corporate_action_events"); op.drop_table("corporate_actions")
