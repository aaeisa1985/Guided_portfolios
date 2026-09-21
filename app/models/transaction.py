from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Transaction(Base):
    __tablename__="transactions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    transaction_type:Mapped[str]=mapped_column(String(30))
    amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    status:Mapped[str]=mapped_column(String(30),default="PENDING")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
