from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class PortfolioSubscription(Base):
    __tablename__="portfolio_subscriptions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    subscription_amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    status:Mapped[str]=mapped_column(String(40),default="CREATED")
    portfolio_version_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("portfolio_versions.id"),index=True,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class SubscriptionEvent(Base):
    __tablename__="subscription_events"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    subscription_id:Mapped[UUID]=mapped_column(ForeignKey("portfolio_subscriptions.id"),index=True)
    event_type:Mapped[str]=mapped_column(String(50))
    event_data:Mapped[str]=mapped_column(Text,default="{}")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
