from fastapi import Depends,Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user,token_for,hash_password,verify_password
from app.models import Customer,InvestmentAccount,RiskAssessment
from app.schemas import RegisterIn,LoginIn,TokenOut
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/auth/register",response_model=TokenOut)
def register(request: Request,x:RegisterIn):
    with Session(engine) as s:
        if s.scalar(select(Customer).where(Customer.email==x.email)): raise HTTPException(409,"Email already registered")
        c=Customer(customer_id="C-"+uuid4().hex[:10].upper(),full_name=x.full_name,email=x.email,mobile=x.mobile,password_hash=pwd.hash(x.password))
        s.add(c); s.flush()
        s.add(InvestmentAccount(customer_id=c.id,account_number="ACC-"+uuid4().hex[:12].upper()))
        s.add(RiskAssessment(customer_id=c.id,risk_score=50,risk_category="BALANCED",expiry_date=datetime.now(timezone.utc)+timedelta(days=365)))
        audit(s,c,"CUSTOMER_REGISTERED","Customer",c.id,request=request); s.commit()
        return {"access_token":token_for(c)}

@router.post("/api/v1/auth/login",response_model=TokenOut)
def login(x:LoginIn):
    with Session(engine) as s:
        c=s.scalar(select(Customer).where(Customer.email==x.email))
        if not c or not pwd.verify(x.password,c.password_hash): raise HTTPException(401,"Invalid credentials")
        return {"access_token":token_for(c)}

@router.get("/api/v1/auth/me")
def me(c=Depends(current_user)):
    with Session(engine) as s:
        r=s.scalar(select(RiskAssessment).where(RiskAssessment.customer_id==c.id).order_by(RiskAssessment.assessment_date.desc()))
        return {"id":c.id,"customerId":c.customer_id,"name":c.full_name,"email":c.email,"investorType":c.investor_type,"kycStatus":c.kyc_status,"amlStatus":c.aml_status,"role":c.role,"riskProfile":None if not r else {"score":r.risk_score,"category":r.risk_category,"expiryDate":r.expiry_date}}
