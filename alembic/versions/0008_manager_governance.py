"""Manager portfolio governance and publication metadata.
Revision ID: 0008_manager_governance
Revises: 0007_corporate_actions
"""
from alembic import op
import sqlalchemy as sa
revision="0008_manager_governance"
down_revision="0007_corporate_actions"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("portfolios",sa.Column("strategy",sa.Text(),nullable=False,server_default=""))
    op.add_column("portfolios",sa.Column("investment_style",sa.String(50),nullable=False,server_default="ACTIVE"))
    op.add_column("portfolios",sa.Column("shariah_status",sa.String(30),nullable=False,server_default="NOT_APPLICABLE"))
    op.add_column("portfolios",sa.Column("distribution_policy",sa.String(80),nullable=False,server_default="ACCUMULATING"))
    op.add_column("portfolios",sa.Column("review_frequency",sa.String(50),nullable=False,server_default="QUARTERLY"))
    op.add_column("portfolios",sa.Column("target_horizon_years",sa.Integer(),nullable=True))
    op.add_column("portfolios",sa.Column("inception_date",sa.DateTime(timezone=True),nullable=True))
    op.add_column("portfolio_versions",sa.Column("created_by",sa.Uuid(),sa.ForeignKey("customers.id"),nullable=True))
    op.add_column("portfolio_versions",sa.Column("notes",sa.Text(),nullable=False,server_default=""))
    op.add_column("portfolio_documents",sa.Column("status",sa.String(30),nullable=False,server_default="PUBLISHED"))
    op.add_column("portfolio_documents",sa.Column("checksum",sa.String(128),nullable=True))
    op.create_index("idx_portfolios_status_risk","portfolios",["status","risk_level"])
    op.create_index("idx_portfolio_versions_portfolio_status","portfolio_versions",["portfolio_id","status"])
    op.create_index("idx_portfolio_documents_portfolio_status","portfolio_documents",["portfolio_id","status"])
    op.create_index("idx_portfolio_versions_created_by","portfolio_versions",["created_by"])

def downgrade():
    op.drop_index("idx_portfolio_versions_created_by","portfolio_versions")
    op.drop_index("idx_portfolio_documents_portfolio_status","portfolio_documents")
    op.drop_index("idx_portfolio_versions_portfolio_status","portfolio_versions")
    op.drop_index("idx_portfolios_status_risk","portfolios")
    op.drop_column("portfolio_documents","checksum")
    op.drop_column("portfolio_documents","status")
    op.drop_column("portfolio_versions","notes")
    op.drop_column("portfolio_versions","created_by")
    op.drop_column("portfolios","inception_date")
    op.drop_column("portfolios","target_horizon_years")
    op.drop_column("portfolios","review_frequency")
    op.drop_column("portfolios","distribution_policy")
    op.drop_column("portfolios","shariah_status")
    op.drop_column("portfolios","investment_style")
    op.drop_column("portfolios","strategy")
