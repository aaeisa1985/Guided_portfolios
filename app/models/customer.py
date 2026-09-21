from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, Role

class Customer(Base):
    __tablename__="customers"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    full_name:Mapped[str]=mapped_column(String(200))
    email:Mapped[str]=mapped_column(String(320),unique=True,index=True)
    mobile:Mapped[Optional[str]]=mapped_column(String(40),nullable=True)
    password_hash:Mapped[str]=mapped_column(String(255))
    investor_type:Mapped[str]=mapped_column(String(40),default="INDIVIDUAL")
    kyc_status:Mapped[str]=mapped_column(String(30),default="PENDING")
    aml_status:Mapped[str]=mapped_column(String(30),default="PENDING")
    role:Mapped[str]=mapped_column(String(30),default=Role.investor.value)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class InvestmentAccount(Base):
    __tablename__="investment_accounts"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    account_number:Mapped[str]=mapped_column(String(50),unique=True,index=True)
    base_currency:Mapped[str]=mapped_column(String(3),default="AED")
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
