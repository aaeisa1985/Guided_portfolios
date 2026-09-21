from datetime import datetime, timedelta, timezone
import os, secrets
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
import hashlib, math

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from passlib.context import CryptContext
from jose import jwt, JWTError

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./data/emcoin.db")
SECRET=os.getenv("EMCOIN_JWT_SECRET")
if not SECRET or SECRET=="dev-only-change-this-secret":
    raise RuntimeError("EMCOIN_JWT_SECRET must be set to a strong secret before starting the API")
ALGORITHM="HS256"
CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:8000,http://127.0.0.1:8000").split(",") if x.strip()]
if DATABASE_URL.startswith("sqlite:///./data/"):
    os.makedirs("data",exist_ok=True)
pwd=CryptContext(schemes=["bcrypt"], deprecated="auto")

class Base(DeclarativeBase): pass
class Role(str,Enum): investor="INVESTOR"; manager="MANAGER"; admin="ADMIN"

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

class RiskAssessment(Base):
    __tablename__="risk_assessments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    risk_score:Mapped[int]=mapped_column()
    risk_category:Mapped[str]=mapped_column(String(40))
    assessment_date:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    expiry_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")

class Portfolio(Base):
    __tablename__="portfolios"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    name:Mapped[str]=mapped_column(String(200))
    slug:Mapped[str]=mapped_column(String(100),unique=True,index=True)
    vehicle_type:Mapped[str]=mapped_column(String(40),default="MODEL_PORTFOLIO")
    category:Mapped[str]=mapped_column(String(60))
    objective:Mapped[str]=mapped_column(Text)
    risk_level:Mapped[int]=mapped_column()
    minimum_investment:Mapped[Decimal]=mapped_column(Numeric(18,2),default=0)
    management_fee:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    performance_fee:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    benchmark:Mapped[Optional[str]]=mapped_column(String(100),nullable=True)
    base_currency:Mapped[str]=mapped_column(String(3),default="AED")
    liquidity_terms:Mapped[str]=mapped_column(String(100),default="Daily")
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")

class PortfolioAllocation(Base):
    __tablename__="portfolio_allocations"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    asset_class:Mapped[str]=mapped_column(String(80))
    target_weight:Mapped[Decimal]=mapped_column(Numeric(8,4))
    min_weight:Mapped[Decimal]=mapped_column(Numeric(8,4),default=0)
    max_weight:Mapped[Decimal]=mapped_column(Numeric(8,4),default=100)

class Instrument(Base):
    __tablename__="instruments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    symbol:Mapped[Optional[str]]=mapped_column(String(80),unique=True,index=True,nullable=True)
    name:Mapped[str]=mapped_column(String(200))
    instrument_type:Mapped[str]=mapped_column(String(50))
    asset_class:Mapped[str]=mapped_column(String(80))
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    isin:Mapped[Optional[str]]=mapped_column(String(20),unique=True,index=True,nullable=True)
    status:Mapped[str]=mapped_column(String(30),default="ACTIVE")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PortfolioVersion(Base):
    __tablename__="portfolio_versions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    version_number:Mapped[int]=mapped_column()
    status:Mapped[str]=mapped_column(String(30),default="DRAFT")
    effective_at:Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
    approved_by:Mapped[Optional[UUID]]=mapped_column(nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class IdempotencyKey(Base):
    __tablename__="idempotency_keys"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    key:Mapped[str]=mapped_column(String(200))
    endpoint:Mapped[str]=mapped_column(String(120))
    response_status:Mapped[int]=mapped_column(default=200)
    response_body:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class LedgerEntry(Base):
    __tablename__="ledger_entries"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    subscription_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("portfolio_subscriptions.id"),index=True,nullable=True)
    transaction_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("transactions.id"),index=True,nullable=True)
    entry_type:Mapped[str]=mapped_column(String(40))
    direction:Mapped[str]=mapped_column(String(10))
    amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    currency:Mapped[str]=mapped_column(String(3),default="AED")
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    description:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PortfolioHolding(Base):
    __tablename__="portfolio_holdings"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    instrument_name:Mapped[str]=mapped_column(String(200))
    instrument_type:Mapped[str]=mapped_column(String(50))
    ticker:Mapped[Optional[str]]=mapped_column(String(50),nullable=True)
    instrument_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("instruments.id"),index=True,nullable=True)
    target_weight:Mapped[Decimal]=mapped_column(Numeric(8,4))

class PortfolioPerformance(Base):
    __tablename__="portfolio_performance"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    date:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    nav:Mapped[Decimal]=mapped_column(Numeric(18,6))
    daily_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)
    monthly_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)
    ytd_return:Mapped[Decimal]=mapped_column(Numeric(10,6),default=0)

class PortfolioDocument(Base):
    __tablename__="portfolio_documents"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    document_type:Mapped[str]=mapped_column(String(50))
    file_url:Mapped[str]=mapped_column(Text)
    version:Mapped[str]=mapped_column(String(30))
    published_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class SuitabilityAssessment(Base):
    __tablename__="suitability_assessments"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    customer_id:Mapped[UUID]=mapped_column(ForeignKey("customers.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    is_suitable:Mapped[bool]=mapped_column(Boolean)
    reason:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PortfolioSubscription(Base):
    __tablename__="portfolio_subscriptions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    subscription_amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    status:Mapped[str]=mapped_column(String(40),default="CREATED")
    portfolio_version_id:Mapped[Optional[UUID]]=mapped_column(ForeignKey("portfolio_versions.id"),index=True,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class SubscriptionEvent(Base):
    __tablename__="subscription_events"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    subscription_id:Mapped[UUID]=mapped_column(ForeignKey("portfolio_subscriptions.id"),index=True)
    event_type:Mapped[str]=mapped_column(String(50))
    event_data:Mapped[str]=mapped_column(Text,default="{}")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

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

class Transaction(Base):
    __tablename__="transactions"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    account_id:Mapped[UUID]=mapped_column(ForeignKey("investment_accounts.id"),index=True)
    portfolio_id:Mapped[UUID]=mapped_column(ForeignKey("portfolios.id"),index=True)
    transaction_type:Mapped[str]=mapped_column(String(30))
    amount:Mapped[Decimal]=mapped_column(Numeric(18,2))
    units:Mapped[Decimal]=mapped_column(Numeric(18,6),default=0)
    status:Mapped[str]=mapped_column(String(30),default="PENDING")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

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
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {},pool_pre_ping=True)


class RegisterIn(BaseModel):
    full_name:str; email:EmailStr; password:str=Field(min_length=8); mobile:Optional[str]=None
class LoginIn(BaseModel): email:EmailStr; password:str
class PortfolioOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID; name:str; slug:str; vehicle_type:str; category:str; objective:str; risk_level:int
    minimum_investment:Decimal; management_fee:Decimal; performance_fee:Decimal; benchmark:Optional[str]
    base_currency:str; liquidity_terms:str; status:str
class SuitabilityIn(BaseModel): portfolio_id:UUID
class SimulatorIn(BaseModel): portfolio_id:UUID; amount:Decimal=Field(gt=0); years:int=Field(ge=1,le=50)
class SubscriptionIn(BaseModel): portfolio_id:UUID; amount:Decimal=Field(gt=0)
class ConsentIn(BaseModel): portfolio_id:UUID; consent_type:str; consent_text:str; accepted:bool
class InstrumentIn(BaseModel): symbol:Optional[str]=None; name:str; instrument_type:str; asset_class:str; currency:str="AED"; isin:Optional[str]=None
class LedgerEntryIn(BaseModel): account_id:UUID; entry_type:str; direction:str; amount:Decimal=Field(gt=0); currency:str="AED"; units:Decimal=Field(default=0,ge=0); description:str=""
class TokenOut(BaseModel): access_token:str; token_type:str="bearer"

app=FastAPI(title="EmCoin Guided Portfolios API",version="1.0.0",description="Institutional-grade Guided Portfolios MVP")
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Request-ID","X-Idempotency-Key"])

@app.middleware("http")
async def security_headers(request, call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["X-Request-ID"]=request.headers.get("X-Request-ID",secrets.token_hex(8))
    return response

def token_for(c:Customer):
    return jwt.encode({"sub":str(c.id),"role":c.role,"exp":datetime.now(timezone.utc)+timedelta(hours=1)},SECRET,algorithm=ALGORITHM)
def current_user(authorization:Optional[str]=Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "): raise HTTPException(401,"Authentication required")
    try: payload=jwt.decode(authorization.split()[1],SECRET,algorithms=[ALGORITHM]); cid=UUID(payload["sub"])
    except (JWTError,ValueError,KeyError): raise HTTPException(401,"Invalid token")
    with Session(engine) as s:
        c=s.get(Customer,cid)
        if not c: raise HTTPException(401,"Customer not found")
        return c
def audit(s,actor,action,entity,entity_id=None):
    s.add(AuditLog(actor_id=actor.id if actor else None,action=action,entity_type=entity,entity_id=str(entity_id) if entity_id else None))

@app.get("/health")
def health(): return {"status":"ok","service":"emcoin-guided-portfolios","version":"1.0.0"}

@app.get("/health/ready")
def readiness():
    with Session(engine) as s:
        s.execute(select(1))
    return {"status":"ready","database":"ok"}

@app.post("/api/v1/auth/register",response_model=TokenOut)
def register(x:RegisterIn):
    with Session(engine) as s:
        if s.scalar(select(Customer).where(Customer.email==x.email)): raise HTTPException(409,"Email already registered")
        c=Customer(customer_id="C-"+uuid4().hex[:10].upper(),full_name=x.full_name,email=x.email,mobile=x.mobile,password_hash=pwd.hash(x.password))
        s.add(c); s.flush()
        s.add(InvestmentAccount(customer_id=c.id,account_number="ACC-"+uuid4().hex[:12].upper()))
        s.add(RiskAssessment(customer_id=c.id,risk_score=50,risk_category="BALANCED",expiry_date=datetime.now(timezone.utc)+timedelta(days=365)))
        audit(s,c,"CUSTOMER_REGISTERED","Customer",c.id); s.commit()
        return {"access_token":token_for(c)}

@app.post("/api/v1/auth/login",response_model=TokenOut)
def login(x:LoginIn):
    with Session(engine) as s:
        c=s.scalar(select(Customer).where(Customer.email==x.email))
        if not c or not pwd.verify(x.password,c.password_hash): raise HTTPException(401,"Invalid credentials")
        return {"access_token":token_for(c)}

@app.get("/api/v1/auth/me")
def me(c=Depends(current_user)):
    with Session(engine) as s:
        r=s.scalar(select(RiskAssessment).where(RiskAssessment.customer_id==c.id).order_by(RiskAssessment.assessment_date.desc()))
        return {"id":c.id,"customerId":c.customer_id,"name":c.full_name,"email":c.email,"investorType":c.investor_type,"kycStatus":c.kyc_status,"amlStatus":c.aml_status,"role":c.role,"riskProfile":None if not r else {"score":r.risk_score,"category":r.risk_category,"expiryDate":r.expiry_date}}

@app.get("/api/v1/portfolios",response_model=list[PortfolioOut])
def portfolios(category:Optional[str]=Query(None),risk_level:Optional[int]=None):
    with Session(engine) as s:
        q=select(Portfolio).where(Portfolio.status=="ACTIVE")
        if category:q=q.where(Portfolio.category==category)
        if risk_level is not None:q=q.where(Portfolio.risk_level==risk_level)
        return list(s.scalars(q).all())

@app.get("/api/v1/portfolios/{portfolio_id}")
def portfolio_detail(portfolio_id:UUID):
    with Session(engine) as s:
        p=s.get(Portfolio,portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        a=list(s.scalars(select(PortfolioAllocation).where(PortfolioAllocation.portfolio_id==p.id)).all())
        h=list(s.scalars(select(PortfolioHolding).where(PortfolioHolding.portfolio_id==p.id)).all())
        perf=list(s.scalars(select(PortfolioPerformance).where(PortfolioPerformance.portfolio_id==p.id).order_by(PortfolioPerformance.date.desc()).limit(30)).all())
        docs=list(s.scalars(select(PortfolioDocument).where(PortfolioDocument.portfolio_id==p.id)).all())
        return {"portfolio":PortfolioOut.model_validate(p),"allocations":a,"holdings":h,"performance":perf,"documents":docs}

@app.post("/api/v1/suitability/check")
def suitability(x:SuitabilityIn,c=Depends(current_user)):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        r=s.scalar(select(RiskAssessment).where(RiskAssessment.customer_id==c.id,RiskAssessment.status=="ACTIVE").order_by(RiskAssessment.assessment_date.desc()))
        if not p or not r: raise HTTPException(404,"Portfolio or active risk assessment not found")
        suitable=r.risk_score>=p.risk_level*20
        reason="Risk profile is compatible with portfolio risk level." if suitable else "Portfolio risk level exceeds the current investor risk capacity."
        a=SuitabilityAssessment(customer_id=c.id,portfolio_id=p.id,is_suitable=suitable,reason=reason); s.add(a); audit(s,c,"SUITABILITY_CHECKED","Portfolio",p.id); s.commit()
        return {"suitable":suitable,"reason":reason,"riskScore":r.risk_score,"portfolioRiskLevel":p.risk_level,"assessmentId":a.id}

@app.post("/api/v1/simulator")
def simulator(x:SimulatorIn):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        expected={1:0.045,2:0.06,3:0.075,4:0.09,5:0.11}.get(p.risk_level,0.075)
        fee=float(p.management_fee)/100
        net=max(0.0,expected-fee)
        return {"initialInvestment":x.amount,"periodYears":x.years,"expectedAnnualReturn":net,"managementFee":float(p.management_fee),"scenarios":{"conservative":float(x.amount)*(1+max(-.05,net-.04))**x.years,"base":float(x.amount)*(1+net)**x.years,"optimistic":float(x.amount)*(1+net+.04)**x.years},"disclaimer":"Illustrative projection only; not a guarantee or investment recommendation."}

@app.post("/api/v1/subscriptions")
def subscribe(x:SubscriptionIn,c=Depends(current_user),x_idempotency_key:Optional[str]=Header(None,alias="X-Idempotency-Key")):
    with Session(engine) as s:
        if x_idempotency_key:
            prior=s.scalar(select(IdempotencyKey).where(IdempotencyKey.customer_id==c.id,IdempotencyKey.key==x_idempotency_key,IdempotencyKey.endpoint=="POST:/api/v1/subscriptions"))
            if prior:
                import json
                return json.loads(prior.response_body)
        p=s.get(Portfolio,x.portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        if x.amount<p.minimum_investment: raise HTTPException(400,f"Minimum investment is {p.minimum_investment} {p.base_currency}")
        account=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id,InvestmentAccount.status=="ACTIVE"))
        if not account: raise HTTPException(404,"Active investment account not found")
        suit=s.scalar(select(SuitabilityAssessment).where(SuitabilityAssessment.customer_id==c.id,SuitabilityAssessment.portfolio_id==p.id).order_by(SuitabilityAssessment.created_at.desc()))
        if not suit or not suit.is_suitable: raise HTTPException(400,"Suitability check must pass before subscription")
        sub=PortfolioSubscription(account_id=account.id,portfolio_id=p.id,subscription_amount=x.amount,status="PAYMENT_PENDING")
        s.add(sub); s.flush()
        version=s.scalar(select(PortfolioVersion).where(PortfolioVersion.portfolio_id==p.id,PortfolioVersion.status=="ACTIVE").order_by(PortfolioVersion.version_number.desc()))
        if version: sub.portfolio_version_id=version.id
        s.add(SubscriptionEvent(subscription_id=sub.id,event_type="CREATED")); s.add(SubscriptionEvent(subscription_id=sub.id,event_type="SUITABILITY_CHECKED")); audit(s,c,"SUBSCRIPTION_CREATED","PortfolioSubscription",sub.id); s.commit()
        return {"subscriptionId":sub.id,"status":sub.status,"portfolioId":sub.portfolio_id,"portfolioVersionId":sub.portfolio_version_id,"amount":sub.subscription_amount,"currency":p.base_currency,"createdAt":sub.created_at}

@app.get("/api/v1/subscriptions")
def subscriptions(c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        if not a:return []
        rows=list(s.scalars(select(PortfolioSubscription).where(PortfolioSubscription.account_id==a.id).order_by(PortfolioSubscription.created_at.desc())).all())
        return [{"id":x.id,"portfolio_id":x.portfolio_id,"portfolio_name":(s.get(Portfolio,x.portfolio_id).name if s.get(Portfolio,x.portfolio_id) else "Portfolio"),"subscription_amount":x.subscription_amount,"units":x.units,"status":x.status,"created_at":x.created_at,"currency":(s.get(Portfolio,x.portfolio_id).base_currency if s.get(Portfolio,x.portfolio_id) else "AED")} for x in rows]

@app.get("/api/v1/subscriptions/{subscription_id}")
def subscription(subscription_id:UUID,c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        sub=s.scalar(select(PortfolioSubscription).where(PortfolioSubscription.id==subscription_id,PortfolioSubscription.account_id==a.id))
        if not sub: raise HTTPException(404,"Subscription not found")
        events=list(s.scalars(select(SubscriptionEvent).where(SubscriptionEvent.subscription_id==sub.id).order_by(SubscriptionEvent.created_at)).all())
        return {"subscription":sub,"events":events}

@app.post("/api/v1/consents")
def consent(x:ConsentIn,c=Depends(current_user)):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        digest=hashlib.sha256(x.consent_text.encode()).hexdigest()
        row=PortfolioConsent(customer_id=c.id,portfolio_id=p.id,consent_type=x.consent_type,consent_text=x.consent_text,accepted=x.accepted,disclosure_hash=digest)
        s.add(row); audit(s,c,"CONSENT_RECORDED","PortfolioConsent",row.id); s.commit()
        return {"consentId":row.id,"accepted":row.accepted,"disclosureHash":digest}

@app.get("/api/v1/activity")
def activity(limit:int=Query(50,ge=1,le=200),c=Depends(current_user)):
    with Session(engine) as s:
        rows=list(s.scalars(select(AuditLog).where(AuditLog.actor_id==c.id).order_by(AuditLog.created_at.desc()).limit(limit)).all())
        return [{"id":x.id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"created_at":x.created_at} for x in rows]

@app.get("/api/v1/dashboard")
def dashboard(c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        subs=[] if not a else list(s.scalars(select(PortfolioSubscription).where(PortfolioSubscription.account_id==a.id)).all())
        invested=sum(float(x.subscription_amount) for x in subs if x.status in ("ALLOCATED","COMPLETED"))
        pending=sum(float(x.subscription_amount) for x in subs if x.status not in ("ALLOCATED","COMPLETED"))
        return {"accountId":None if not a else a.id,"aum":invested,"marketValue":invested,"profitLoss":0,"pendingSubscriptions":pending,"portfolioCount":len(subs)}

@app.post("/api/v1/admin/seed")
def seed(c=Depends(current_user)):
    if c.role not in (Role.admin.value,Role.manager.value): raise HTTPException(403,"Admin or manager required")
    with Session(engine) as s:
        if s.scalar(select(Portfolio)): return {"status":"already_seeded"}
        data=[
          ("EmCoin Fixed Income","fixed-income","INCOME","Capital preservation and diversified income generation.",2,0.25),
          ("EmCoin Balanced Growth","balanced-growth","BALANCED","Diversified long-term growth across defensive and growth assets.",3,0.75),
          ("EmCoin Growth","growth","GROWTH","Long-term capital appreciation with higher volatility.",4,1.00),
          ("EmCoin Digital Assets","digital-assets","ALTERNATIVES","Diversified digital-asset exposure with high volatility.",5,1.50)]
        for name,slug,cat,obj,risk,fee in data:
            p=Portfolio(name=name,slug=slug,category=cat,objective=obj,risk_level=risk,minimum_investment=Decimal("1000"),management_fee=Decimal(str(fee)),benchmark="Internal blended benchmark",liquidity_terms="Daily")
            s.add(p); s.flush()
            s.add(PortfolioAllocation(portfolio_id=p.id,asset_class="Primary Allocation",target_weight=Decimal("100")))
            s.add(PortfolioPerformance(portfolio_id=p.id,nav=Decimal("100"),daily_return=Decimal("0"),monthly_return=Decimal("0"),ytd_return=Decimal("0")))
        audit(s,c,"PORTFOLIO_CATALOG_SEEDED","Portfolio"); s.commit()
        return {"status":"seeded","count":len(data)}

@app.get("/api/v1/admin/audit")
def audit_logs(c=Depends(current_user),limit:int=Query(100,le=500)):
    if c.role not in (Role.admin.value,Role.manager.value): raise HTTPException(403,"Admin or manager required")
    with Session(engine) as s:return list(s.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all())

def require_staff(c):
    if c.role not in (Role.admin.value,Role.manager.value):
        raise HTTPException(403,"Manager or admin role required")

@app.post("/api/v1/admin/instruments")
def create_instrument(x:InstrumentIn,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if x.symbol and s.scalar(select(Instrument).where(Instrument.symbol==x.symbol)): raise HTTPException(409,"Instrument symbol already exists")
        i=Instrument(**x.model_dump()); s.add(i); s.flush(); audit(s,c,"INSTRUMENT_CREATED","Instrument",i.id); s.commit()
        return {"id":i.id,"symbol":i.symbol,"name":i.name,"status":i.status}

@app.get("/api/v1/admin/instruments")
def list_instruments(c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        return list(s.scalars(select(Instrument).order_by(Instrument.name)).all())

@app.post("/api/v1/admin/portfolios/{portfolio_id}/versions")
def create_portfolio_version(portfolio_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if not s.get(Portfolio,portfolio_id): raise HTTPException(404,"Portfolio not found")
        n=(s.scalar(select(PortfolioVersion.version_number).where(PortfolioVersion.portfolio_id==portfolio_id).order_by(PortfolioVersion.version_number.desc())) or 0)+1
        v=PortfolioVersion(portfolio_id=portfolio_id,version_number=n,status="DRAFT"); s.add(v); s.flush(); audit(s,c,"PORTFOLIO_VERSION_CREATED","PortfolioVersion",v.id); s.commit()
        return {"id":v.id,"portfolioId":portfolio_id,"versionNumber":n,"status":v.status}

@app.post("/api/v1/admin/portfolios/{portfolio_id}/versions/{version_id}/approve")
def approve_portfolio_version(portfolio_id:UUID,version_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        v=s.scalar(select(PortfolioVersion).where(PortfolioVersion.id==version_id,PortfolioVersion.portfolio_id==portfolio_id))
        if not v: raise HTTPException(404,"Portfolio version not found")
        for a in s.scalars(select(PortfolioVersion).where(PortfolioVersion.portfolio_id==portfolio_id,PortfolioVersion.status=="ACTIVE")).all(): a.status="SUPERSEDED"
        v.status="ACTIVE"; v.effective_at=datetime.now(timezone.utc); v.approved_by=c.id
        audit(s,c,"PORTFOLIO_VERSION_APPROVED","PortfolioVersion",v.id); s.commit()
        return {"id":v.id,"versionNumber":v.version_number,"status":v.status,"effectiveAt":v.effective_at}

@app.post("/api/v1/admin/ledger")
def create_ledger_entry(x:LedgerEntryIn,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if not s.get(InvestmentAccount,x.account_id): raise HTTPException(404,"Investment account not found")
        e=LedgerEntry(**x.model_dump()); s.add(e); s.flush(); audit(s,c,"LEDGER_ENTRY_CREATED","LedgerEntry",e.id); s.commit()
        return {"id":e.id,"accountId":e.account_id,"entryType":e.entry_type,"direction":e.direction,"amount":e.amount,"currency":e.currency}

@app.get("/api/v1/admin/ledger/{account_id}")
def account_ledger(account_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        rows=list(s.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_id).order_by(LedgerEntry.created_at)).all())
        balance=sum((x.amount if x.direction=="CREDIT" else -x.amount) for x in rows)
        return {"accountId":account_id,"balance":balance,"entries":rows}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/", include_in_schema=False)
def frontend_home():
    return FileResponse("frontend/index.html")
