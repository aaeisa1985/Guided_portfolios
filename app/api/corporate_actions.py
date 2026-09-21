"""Corporate actions administration API."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import CorporateAction, Instrument, CorporateActionEvent
from app.services.corporate_actions import process_corporate_action, approve_corporate_action
from app.services.audit import audit
router=APIRouter(prefix="/api/v1/admin/corporate-actions",tags=["Corporate Actions"])
VALID={"SPLIT","REVERSE_SPLIT","CASH_DIVIDEND","STOCK_DIVIDEND","RIGHTS_ISSUE","MERGER"}
class CorporateActionIn(BaseModel):
    instrument_id:UUID; action_type:str; ex_date:datetime; effective_date:datetime; record_date:Optional[datetime]=None; payment_date:Optional[datetime]=None
    ratio_numerator:Optional[Decimal]=Field(default=None,gt=0); ratio_denominator:Optional[Decimal]=Field(default=None,gt=0); dividend_per_share:Optional[Decimal]=Field(default=None,ge=0)
    subscription_price:Optional[Decimal]=Field(default=None,ge=0); replacement_instrument_id:Optional[UUID]=None; exchange_ratio:Optional[Decimal]=Field(default=None,gt=0); description:str=""
    @model_validator(mode="after")
    def normalize(self):
        self.action_type=self.action_type.upper()
        if self.action_type not in VALID: raise ValueError("Unsupported corporate action type")
        return self
def _guard(c):
    if c.role not in ("ADMIN","MANAGER"): raise HTTPException(403,"Admin or manager role required")
@router.post("",status_code=201)
def create(x:CorporateActionIn,c=Depends(current_user)):
    _guard(c)
    with Session(engine) as s:
        if not s.get(Instrument,x.instrument_id): raise HTTPException(404,"Instrument not found")
        ca=CorporateAction(**x.model_dump(),created_by=c.id); s.add(ca); s.flush(); audit(s,c,"CORPORATE_ACTION_CREATED","CorporateAction",ca.id); s.commit()
        return {"id":str(ca.id),"status":ca.status,"actionType":ca.action_type}
@router.post("/{action_id}/approve")
def approve(action_id:UUID,request:Request,c=Depends(current_user)):
    _guard(c)
    with Session(engine) as s:
        ca=s.get(CorporateAction,action_id)
        if not ca: raise HTTPException(404,"Corporate action not found")
        try: approve_corporate_action(s,ca,c); audit(s,c,"CORPORATE_ACTION_APPROVED","CorporateAction",ca.id,request); s.commit()
        except ValueError as e: s.rollback(); raise HTTPException(400,str(e))
        return {"id":str(ca.id),"status":ca.status,"approvedBy":str(ca.approved_by)}
@router.post("/{action_id}/execute")
def execute(action_id:UUID,request:Request,c=Depends(current_user)):
    _guard(c)
    with Session(engine) as s:
        ca=s.get(CorporateAction,action_id)
        if not ca: raise HTTPException(404,"Corporate action not found")
        try: events=process_corporate_action(s,ca); audit(s,c,"CORPORATE_ACTION_EXECUTED","CorporateAction",ca.id,request); s.commit()
        except ValueError as e: s.rollback(); raise HTTPException(400,str(e))
        return {"id":str(ca.id),"status":ca.status,"eventsProcessed":len(events),"executedAt":ca.executed_at}
@router.get("")
def list_actions(status:Optional[str]=None,instrument_id:Optional[UUID]=None,c=Depends(current_user)):
    _guard(c)
    with Session(engine) as s:
        q=select(CorporateAction).order_by(CorporateAction.ex_date.desc())
        if status:q=q.where(CorporateAction.status==status.upper())
        if instrument_id:q=q.where(CorporateAction.instrument_id==instrument_id)
        return [{"id":str(a.id),"instrumentId":str(a.instrument_id),"actionType":a.action_type,"status":a.status,"exDate":a.ex_date,"effectiveDate":a.effective_date,"paymentDate":a.payment_date,"description":a.description,"failureReason":a.failure_reason} for a in s.scalars(q).all()]
@router.get("/{action_id}/events")
def events(action_id:UUID,c=Depends(current_user)):
    _guard(c)
    with Session(engine) as s:
        if not s.get(CorporateAction,action_id): raise HTTPException(404,"Corporate action not found")
        return [{"id":str(e.id),"positionId":str(e.position_id),"quantityBefore":str(e.quantity_before),"quantityAfter":str(e.quantity_after),"cashImpact":str(e.cash_impact),"incomeRecognized":str(e.income_recognized),"cashInLieu":str(e.cash_in_lieu)} for e in s.scalars(select(CorporateActionEvent).where(CorporateActionEvent.corporate_action_id==action_id)).all()]
