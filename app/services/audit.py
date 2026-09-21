from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models import AuditLog
def audit(session:Session,actor,action,entity,entity_id=None,request:Optional[Request]=None):
    session.add(AuditLog(actor_id=actor.id if actor else None,action=action,entity_type=entity,entity_id=str(entity_id) if entity_id else None,ip_address=request.client.host if request and request.client else None,user_agent=request.headers.get("user-agent") if request else None))
