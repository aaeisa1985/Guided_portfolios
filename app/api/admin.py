from datetime import datetime,timezone
from typing import Optional
from uuid import UUID
from fastapi import Depends,Header,HTTPException,Query,Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import *
from app.schemas import InstrumentIn,LedgerEntryIn,OrderIn
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/admin/seed")
def seed(request: Request,c=Depends(current_user)):
    if c.role not in (Role.admin.value,Role.manager.value): raise HTTPException(403,"Admin or manager required")
    with Session(engine) as s:
        if s.scalar(select(Portfolio)): return {"status":"already_seeded"}
        data=[
          ("X Company Fixed Income","fixed-income","INCOME","Capital preservation and diversified income generation.",2,0.25),
          ("X Company Balanced Growth","balanced-growth","BALANCED","Diversified long-term growth across defensive and growth assets.",3,0.75),
          ("X Company Growth","growth","GROWTH","Long-term capital appreciation with higher volatility.",4,1.00),
          ("X Company Digital Assets","digital-assets","ALTERNATIVES","Diversified digital-asset exposure with high volatility.",5,1.50)]
        for name,slug,cat,obj,risk,fee in data:
            p=Portfolio(name=name,slug=slug,category=cat,objective=obj,risk_level=risk,minimum_investment=Decimal("1000"),management_fee=Decimal(str(fee)),benchmark="Internal blended benchmark",liquidity_terms="Daily")
            s.add(p); s.flush()
            s.add(PortfolioAllocation(portfolio_id=p.id,asset_class="Primary Allocation",target_weight=Decimal("100")))
            s.add(PortfolioPerformance(portfolio_id=p.id,nav=Decimal("100"),daily_return=Decimal("0"),monthly_return=Decimal("0"),ytd_return=Decimal("0")))
        audit(s,c,"PORTFOLIO_CATALOG_SEEDED","Portfolio",request=request); s.commit()
        return {"status":"seeded","count":len(data)}

@router.get("/api/v1/admin/audit")
def audit_logs(c=Depends(current_user),limit:int=Query(100,le=500)):
    if c.role not in (Role.admin.value,Role.manager.value): raise HTTPException(403,"Admin or manager required")
    with Session(engine) as s:return list(s.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all())

def require_staff(c):
    if c.role not in (Role.admin.value,Role.manager.value):
        raise HTTPException(403,"Manager or admin role required")

@router.post("/api/v1/admin/instruments")
def create_instrument(request: Request,x:InstrumentIn,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if x.symbol and s.scalar(select(Instrument).where(Instrument.symbol==x.symbol)): raise HTTPException(409,"Instrument symbol already exists")
        i=Instrument(**x.model_dump()); s.add(i); s.flush(); audit(s,c,"INSTRUMENT_CREATED","Instrument",i.id,request=request); s.commit()
        return {"id":i.id,"symbol":i.symbol,"name":i.name,"status":i.status}

@router.get("/api/v1/admin/instruments")
def list_instruments(c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        return list(s.scalars(select(Instrument).order_by(Instrument.name)).all())

@router.post("/api/v1/admin/portfolios/{portfolio_id}/versions")
def create_portfolio_version(request: Request,portfolio_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if not s.get(Portfolio,portfolio_id): raise HTTPException(404,"Portfolio not found")
        n=(s.scalar(select(PortfolioVersion.version_number).where(PortfolioVersion.portfolio_id==portfolio_id).order_by(PortfolioVersion.version_number.desc())) or 0)+1
        v=PortfolioVersion(portfolio_id=portfolio_id,version_number=n,status="DRAFT"); s.add(v); s.flush(); audit(s,c,"PORTFOLIO_VERSION_CREATED","PortfolioVersion",v.id,request=request); s.commit()
        return {"id":v.id,"portfolioId":portfolio_id,"versionNumber":n,"status":v.status}

@router.post("/api/v1/admin/portfolios/{portfolio_id}/versions/{version_id}/approve")
def approve_portfolio_version(request: Request,portfolio_id:UUID,version_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        v=s.scalar(select(PortfolioVersion).where(PortfolioVersion.id==version_id,PortfolioVersion.portfolio_id==portfolio_id))
        if not v: raise HTTPException(404,"Portfolio version not found")
        for a in s.scalars(select(PortfolioVersion).where(PortfolioVersion.portfolio_id==portfolio_id,PortfolioVersion.status=="ACTIVE")).all(): a.status="SUPERSEDED"
        v.status="ACTIVE"; v.effective_at=datetime.now(timezone.utc); v.approved_by=c.id
        audit(s,c,"PORTFOLIO_VERSION_APPROVED","PortfolioVersion",v.id,request=request); s.commit()
        return {"id":v.id,"versionNumber":v.version_number,"status":v.status,"effectiveAt":v.effective_at}

@router.post("/api/v1/admin/orders")
def create_order(request: Request,x:OrderIn,c=Depends(current_user),x_idempotency_key:Optional[str]=Header(None,alias="X-Idempotency-Key")):
    require_staff(c)
    side=x.side.upper()
    if side not in ("BUY","SELL"): raise HTTPException(400,"Order side must be BUY or SELL")
    with Session(engine) as s:
        account=s.get(InvestmentAccount,x.account_id)
        if not account: raise HTTPException(404,"Investment account not found")
        if not s.get(Portfolio,x.portfolio_id): raise HTTPException(404,"Portfolio not found")
        if not s.get(Instrument,x.instrument_id): raise HTTPException(404,"Instrument not found")
        if x_idempotency_key:
            prior=s.scalar(select(InvestmentOrder).where(InvestmentOrder.idempotency_key==x_idempotency_key))
            if prior: return {"id":prior.id,"status":prior.status,"replayed":True}
        o=InvestmentOrder(account_id=x.account_id,portfolio_id=x.portfolio_id,instrument_id=x.instrument_id,side=side,order_type=x.order_type.upper(),quantity=x.quantity,limit_price=x.limit_price,idempotency_key=x_idempotency_key,status="PENDING")
        s.add(o); s.flush(); audit(s,c,"ORDER_CREATED","InvestmentOrder",o.id,request=request); s.commit()
        return {"id":o.id,"status":o.status,"side":o.side,"quantity":o.quantity,"createdAt":o.created_at}

@router.post("/api/v1/admin/orders/{order_id}/cancel")
def cancel_order(request: Request,order_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        o=s.get(InvestmentOrder,order_id)
        if not o: raise HTTPException(404,"Order not found")
        if o.status not in ("PENDING","PROCESSING"): raise HTTPException(400,"Only pending or processing orders can be cancelled")
        o.status="CANCELLED"; audit(s,c,"ORDER_CANCELLED","InvestmentOrder",o.id,request=request); s.commit()
        return {"id":o.id,"status":o.status}

@router.post("/api/v1/admin/ledger")
def create_ledger_entry(request: Request,x:LedgerEntryIn,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        if not s.get(InvestmentAccount,x.account_id): raise HTTPException(404,"Investment account not found")
        e=LedgerEntry(**x.model_dump()); s.add(e); s.flush(); audit(s,c,"LEDGER_ENTRY_CREATED","LedgerEntry",e.id,request=request); s.commit()
        return {"id":e.id,"accountId":e.account_id,"entryType":e.entry_type,"direction":e.direction,"amount":e.amount,"currency":e.currency}

@router.get("/api/v1/admin/ledger/{account_id}")
def account_ledger(account_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        rows=list(s.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_id).order_by(LedgerEntry.created_at)).all())
        balance=sum((x.amount if x.direction=="CREDIT" else -x.amount) for x in rows)
        return {"accountId":account_id,"balance":balance,"entries":rows}


