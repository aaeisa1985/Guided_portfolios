from datetime import datetime,timezone
from typing import Optional
from uuid import UUID,uuid4
from sqlalchemy import String,DateTime,Text
from sqlalchemy.orm import Mapped,mapped_column
from .base import Base
class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    actor_id:Mapped[Optional[UUID]]=mapped_column(nullable=True)
    actor_type:Mapped[str]=mapped_column(String(30),default="CUSTOMER")
    action:Mapped[str]=mapped_column(String(100))
    entity_type:Mapped[str]=mapped_column(String(80))
    entity_id:Mapped[Optional[str]]=mapped_column(String(100),nullable=True)
    old_value:Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    new_value:Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    ip_address:Mapped[Optional[str]]=mapped_column(String(64),nullable=True)
    user_agent:Mapped[Optional[str]]=mapped_column(String(512),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
