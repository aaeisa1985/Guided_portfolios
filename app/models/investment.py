from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Instrument(Base):
    __tablename__="instruments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    symbol:Mapped[Optional[str]]=mapped_column(String(80),unique=True,index=True,nullable=True)
    name:Mapped[str]=mapped_column(String(200))
    instrument_type:Mapped[str]=mapped_column(String(50))
    asset_class:Mapped[str]=mapped_column(String(80))
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    isin:Mapped[Optional[str]]=mapped_column(String(20),unique=True,index=True,nullable=True)
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PortfolioVersion(Base):
    __tablename__="portfolio_versions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    version_number:Mapped[int]=mapped_column()
    status:Mapped[str]=mapped_column(String(30),default="DRAFT")
    effective_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    approved_by:Mapped[Optional[UUID]]=mapped_column(nullable=True)
    created_by:Mapped[Optional[UUID]]=mapped_column(ForeignKey("customers.id"),nullable=True,index=True)
    notes:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class IdempotencyKey(Base):
    __tablename__="idempotency_keys"
    __table_args__=(UniqueConstraint("customer_id","key","endpoint",name="uq_idempotency_customer_key_endpoint"),)
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    key:Mapped[str]=mapped_column(String(200))
    endpoint:Mapped[str]=mapped_column(String(120))
    response_status:Mapped[int]=mapped_column(default=200)
    response_body:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class LedgerEntry(Base):
    __tablename__="ledger_entries"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    subscription_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("portfolio_subscriptions.id"),index=True,nullable=True)
    transaction_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("transactions.id"),index=True,nullable=True)
    journal_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("ledger_journals.id"),index=True,nullable=True)
    ledger_account:Mapped[Optional[str]]=mapped_column(String(80),nullable=True)
    entry_type:Mapped[str]=mapped_column(String(40))
    direction:Mapped[str]=mapped_column(String(10))
    amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    description:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PortfolioPosition(Base):
    __tablename__="portfolio_positions"
    __table_args__=(UniqueConstraint("account_id","portfolio_id","instrument_id",name="uq_portfolio_position_key"),)
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    instrument_id:Mapped[UUID]=mapped_column(ForeignKey("instruments.id"),index=True)
    quantity:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    average_cost:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    market_price:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    realized_pnl:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    price_as_of:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    price_source:Mapped[str]=mapped_column(String(120),default="INTERNAL")
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class InvestmentOrder(Base):
    __tablename__="investment_orders"
    __table_args__=(UniqueConstraint("idempotency_key",name="uq_investment_order_idempotency_key"),)
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    instrument_id:Mapped[UUID]=mapped_column(ForeignKey("instruments.id"),index=True)
    side:Mapped[str]=mapped_column(String(10))
    order_type:Mapped[str]=mapped_column(String(20),default="MARKET")
    quantity:Mapped[Decimal]=mapped_column(Numeric(24,8),default=0)
    limit_price:Mapped[Optional[Decimal]]=mapped_column(Numeric(24,8),nullable=True)
    status:Mapped[str]=mapped_column(String(30),default="PENDING")
    idempotency_key:Mapped[Optional[str]]=mapped_column(String(200),nullable=True,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class LedgerJournal(Base):
    __tablename__="ledger_journals"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    reference_type:Mapped[str]=mapped_column(String(50))
    reference_id:Mapped[Optional[UUID]]=mapped_column(nullable=True,index=True)
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    description:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class ExecutionFill(Base):
    __tablename__="execution_fills"
    __table_args__=(UniqueConstraint("execution_id",name="uq_execution_fill_execution_id"),)
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    order_id:Mapped[UUID]=mapped_column(ForeignKey("investment_orders.id"),index=True)
    execution_id:Mapped[str]=mapped_column(String(200))
    quantity:Mapped[Decimal]=mapped_column(Numeric(24,8))
    price:Mapped[Decimal]=mapped_column(Numeric(24,8))
    fees:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    executed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class ValuationSnapshot(Base):
    __tablename__="valuation_snapshots"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("portfolios.id"),index=True,nullable=True)
    as_of:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
    cash_value:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    market_value:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    nav:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    price_source:Mapped[str]=mapped_column(String(120),default="INTERNAL")
