"""Production-grade corporate action domain models."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
class CorporateAction(Base):
    __tablename__="corporate_actions"
    __table_args__=(UniqueConstraint("instrument_id","action_type","ex_date",name="uq_corporate_action_key"),CheckConstraint("action_type IN ('SPLIT','REVERSE_SPLIT','CASH_DIVIDEND','STOCK_DIVIDEND','RIGHTS_ISSUE','MERGER')",name="ck_corporate_action_type"))
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    instrument_id:Mapped[UUID]=mapped_column(ForeignKey("instruments.id"),index=True)
    action_type:Mapped[str]=mapped_column(String(30))
    status:Mapped[str]=mapped_column(String(20),default="DRAFT",index=True)
    ex_date:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    record_date:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    payment_date:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    effective_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    ratio_numerator:Mapped[Optional[Decimal]]=mapped_column(Numeric(18,8),nullable=True)
    ratio_denominator:Mapped[Optional[Decimal]]=mapped_column(Numeric(18,8),nullable=True)
    dividend_per_share:Mapped[Optional[Decimal]]=mapped_column(Numeric(24,8),nullable=True)
    subscription_price:Mapped[Optional[Decimal]]=mapped_column(Numeric(24,8),nullable=True)
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    replacement_instrument_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("instruments.id"),nullable=True)
    exchange_ratio:Mapped[Optional[Decimal]]=mapped_column(Numeric(18,8),nullable=True)
    description:Mapped[str]=mapped_column(Text,default="")
    failure_reason:Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    approved_by:Mapped[Optional[UUID]]=mapped_column(ForeignKey("customers.id"),nullable=True)
    approved_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    executed_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    created_by:Mapped[UUID]=mapped_column(ForeignKey("customers.id"))
class CorporateActionEvent(Base):
    __tablename__="corporate_action_events"
    __table_args__=(UniqueConstraint("corporate_action_id","position_id",name="uq_corporate_action_event_key"),)
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    corporate_action_id:Mapped[UUID]=mapped_column(ForeignKey("corporate_actions.id"),index=True)
    position_id:Mapped[UUID]=mapped_column(ForeignKey("portfolio_positions.id"),index=True)
    journal_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("ledger_journals.id"),index=True,nullable=True)
    quantity_before:Mapped[Decimal]=mapped_column(Numeric(24,8))
    quantity_after:Mapped[Decimal]=mapped_column(Numeric(24,8))
    price_before:Mapped[Decimal]=mapped_column(Numeric(24,8))
    price_after:Mapped[Decimal]=mapped_column(Numeric(24,8))
    average_cost_before:Mapped[Decimal]=mapped_column(Numeric(24,8))
    average_cost_after:Mapped[Decimal]=mapped_column(Numeric(24,8))
    cash_impact:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    income_recognized:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    fractional_units:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    cash_in_lieu:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
