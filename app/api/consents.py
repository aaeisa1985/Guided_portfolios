import hashlib
from datetime import datetime,timezone
from uuid import UUID
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import Portfolio,PortfolioConsent
from app.schemas import ConsentIn
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/consents")
def consent(request: Request,x:ConsentIn,c=Depends(current_user)):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        digest=hashlib.sha256(x.consent_text.encode()).hexdigest()
        row=PortfolioConsent(customer_id=c.id,portfolio_id=p.id,consent_type=x.consent_type,consent_text=x.consent_text,accepted=x.accepted,disclosure_hash=digest)
        s.add(row); audit(s,c,"CONSENT_RECORDED","PortfolioConsent",row.id,request=request); s.commit()
        return {"consentId":row.id,"accepted":row.accepted,"disclosureHash":digest}
