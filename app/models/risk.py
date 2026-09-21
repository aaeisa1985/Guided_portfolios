from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class RiskAssessment(Base):
    __tablename__="risk_assessments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    risk_score:Mapped[int]=mapped_column()
    risk_category:Mapped[str]=mapped_column(String(40))
    assessment_date:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    expiry_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")

class SuitabilityAssessment(Base):
    __tablename__="suitability_assessments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    is_suitable:Mapped[bool]=mapped_column(Boolean)
    reason:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
