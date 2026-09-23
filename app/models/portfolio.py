from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Portfolio(Base):
    __tablename__="portfolios"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    name:Mapped[str]=mapped_column(String(200))
    slug:Mapped[str]=mapped_column(String(100),unique=True,index=True)
    vehicle_type:Mapped[str]=mapped_column(String(40),default="MODEL_PORTFOLIO")
    category:Mapped[str]=mapped_column(String(60))
    objective:Mapped[str]=mapped_column(Text)
    risk_level:Mapped[int]=mapped_column()
    minimum_investment:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    management_fee:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    performance_fee:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    cost_basis_method:Mapped[str]=mapped_column(String(30),default="AVERAGE_COST")
    benchmark:Mapped[Optional[str]]=mapped_column(String(100),nullable=True)
    base_currency:Mapped[str]=mapped_column(String(3),default="AED")
    liquidity_terms:Mapped[str]=mapped_column(String(100),default="Daily")
    status:Mapped[str]=mapped_column(String(30),default="DRAFT")
    strategy:Mapped[str]=mapped_column(Text,default="")
    investment_style:Mapped[str]=mapped_column(String(50),default="ACTIVE")
    shariah_status:Mapped[str]=mapped_column(String(30),default="NOT_APPLICABLE")
    distribution_policy:Mapped[str]=mapped_column(String(80),default="ACCUMULATING")
    review_frequency:Mapped[str]=mapped_column(String(50),default="QUARTERLY")
    target_horizon_years:Mapped[Optional[int]]=mapped_column(nullable=True)
    inception_date:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)

class PortfolioAllocation(Base):
    __tablename__="portfolio_allocations"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    asset_class:Mapped[str]=mapped_column(String(80))
    target_weight:Mapped[Decimal]=mapped_column(Numeric(8,4))
    min_weight:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    max_weight:Mapped[Decimal]=mapped_column(Numeric(8,4),default=100)

class PortfolioHolding(Base):
    __tablename__="portfolio_holdings"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    instrument_name:Mapped[str]=mapped_column(String(200))
    instrument_type:Mapped[str]=mapped_column(String(50))
    ticker:Mapped[Optional[str]]=mapped_column(String(50),nullable=True)
    instrument_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("instruments.id"),index=True,nullable=True)
    target_weight:Mapped[Decimal]=mapped_column(Numeric(8,4))

class PortfolioPerformance(Base):
    __tablename__="portfolio_performance"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    date:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    nav:Mapped[Decimal]=mapped_column(Numeric(18,6))
    daily_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)
    monthly_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)
    ytd_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)

class PortfolioDocument(Base):
    __tablename__="portfolio_documents"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    document_type:Mapped[str]=mapped_column(String(50))
    file_url:Mapped[str]=mapped_column(Text)
    version:Mapped[str]=mapped_column(String(30))
    published_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    status:Mapped[str]=mapped_column(String(30),default="PUBLISHED")
    checksum:Mapped[Optional[str]]=mapped_column(String(128),nullable=True)
