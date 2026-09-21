from datetime import datetime,timezone
from uuid import UUID
from fastapi import Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import Portfolio,RiskAssessment,SuitabilityAssessment
from app.schemas import SuitabilityIn
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/suitability/check")
def suitability(request: Request,x:SuitabilityIn,c=Depends(current_user)):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        r=s.scalar(select(RiskAssessment).where(RiskAssessment.customer_id==c.id,RiskAssessment.status=="ACTIVE",RiskAssessment.expiry_date>datetime.now(timezone.utc)).order_by(RiskAssessment.assessment_date.desc()))
        if not p or not r: raise HTTPException(404,"Portfolio or active risk assessment not found")
        suitable=r.risk_score>=p.risk_level*20
        reason="Risk profile is compatible with portfolio risk level." if suitable else "Portfolio risk level exceeds the current investor risk capacity."
        a=SuitabilityAssessment(customer_id=c.id,portfolio_id=p.id,is_suitable=suitable,reason=reason); s.add(a); audit(s,c,"SUITABILITY_CHECKED","Portfolio",p.id,request=request); s.commit()
        return {"suitable":suitable,"reason":reason,"riskScore":r.risk_score,"portfolioRiskLevel":p.risk_level,"assessmentId":a.id}
