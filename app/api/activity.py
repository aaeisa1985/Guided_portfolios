from fastapi import Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import AuditLog
from fastapi import APIRouter
router=APIRouter()

@router.get("/api/v1/activity")
def activity(limit:int=Query(50,ge=1,le=200),c=Depends(current_user)):
    with Session(engine) as s:
        rows=list(s.scalars(select(AuditLog).where(AuditLog.actor_id==c.id).order_by(AuditLog.created_at.desc()).limit(limit)).all())
        return [{"id":x.id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"created_at":x.created_at} for x in rows]
