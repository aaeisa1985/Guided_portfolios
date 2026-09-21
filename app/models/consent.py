from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class PortfolioConsent(Base):
    __tablename__="portfolio_consents"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    consent_type:Mapped[str]=mapped_column(String(60))
    consent_text:Mapped[str]=mapped_column(Text)
    accepted:Mapped[bool]=mapped_column(Boolean)
    accepted_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    disclosure_hash:Mapped[str]=mapped_column(String(64))
