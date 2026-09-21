from datetime import datetime,timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import Depends,Header,HTTPException,Query,Request
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user,current_admin,admin_token_for
from app.models import *
from app.schemas import InstrumentIn,LedgerEntryIn,OrderIn,ExecutionIn,AdminLoginIn,PortfolioCreateIn,PortfolioUpdateIn,AdminUserUpdateIn,AdminPortfolioResponse
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

from secrets import compare_digest
from app.core.config import ADMIN_USERNAME,ADMIN_PASSWORD

def _admin_audit(session,admin,action,entity,entity_id=None,request=None):
    session.add(AuditLog(
        actor_id=None,
        actor_type="ADMIN",
        action=action,
        entity_type=entity,
        entity_id=str(entity_id) if entity_id else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    ))

@router.post("/api/v1/admin/auth/login")
def admin_login(x:AdminLoginIn):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"Admin credentials are not configured")
    if not compare_digest(x.username,ADMIN_USERNAME) or not compare_digest(x.password,ADMIN_PASSWORD):
        raise HTTPException(401,"Invalid admin credentials")
    return {"access_token":admin_token_for(x.username),"token_type":"bearer"}

@router.get("/api/v1/admin/auth/me")
def admin_me(admin=Depends(current_admin)):
    return admin

@router.get("/api/v1/admin/overview")
def admin_overview(admin=Depends(current_admin)):
    with Session(engine) as s:
        users=s.scalar(select(func.count()).select_from(Customer)) or 0
        active_portfolios=s.scalar(select(func.count()).select_from(Portfolio).where(Portfolio.status=="ACTIVE")) or 0
        total_portfolios=s.scalar(select(func.count()).select_from(Portfolio)) or 0
        subscriptions=s.scalar(select(func.count()).select_from(PortfolioSubscription)) or 0
        pending=s.scalar(select(func.count()).select_from(PortfolioSubscription).where(PortfolioSubscription.status.not_in(["ALLOCATED","COMPLETED"]))) or 0
        return {"users":users,"activePortfolios":active_portfolios,"totalPortfolios":total_portfolios,"subscriptions":subscriptions,"pendingSubscriptions":pending}

@router.get("/api/v1/admin/users")
def admin_users(search:str|None=Query(None),admin=Depends(current_admin)):
    with Session(engine) as s:
        q=select(Customer).order_by(Customer.created_at.desc())
        if search:
            term="%"+search.strip()+"%"
            q=q.where(Customer.full_name.ilike(term) | Customer.email.ilike(term) | Customer.customer_id.ilike(term))
        rows=s.scalars(q.limit(500)).all()
        return [{"id":u.id,"customerId":u.customer_id,"fullName":u.full_name,"email":u.email,"mobile":u.mobile,"investorType":u.investor_type,"kycStatus":u.kyc_status,"amlStatus":u.aml_status,"role":u.role,"createdAt":u.created_at} for u in rows]

@router.patch("/api/v1/admin/users/{user_id}")
def admin_update_user(request:Request,user_id:UUID,x:AdminUserUpdateIn,admin=Depends(current_admin)):
    with Session(engine) as s:
        u=s.get(Customer,user_id)
        if not u: raise HTTPException(404,"User not found")
        changes=x.model_dump(exclude_unset=True)
        for k,v in changes.items(): setattr(u,k,v)
        _admin_audit(s,admin,"ADMIN_USER_UPDATED","Customer",u.id,request)
        s.commit()
        return {"id":u.id,"customerId":u.customer_id,"fullName":u.full_name,"email":u.email,"mobile":u.mobile,"investorType":u.investor_type,"kycStatus":u.kyc_status,"amlStatus":u.aml_status,"role":u.role}

@router.get("/api/v1/admin/portfolios",response_model=list[AdminPortfolioResponse])
def admin_portfolios(admin=Depends(current_admin)):
    with Session(engine) as s:
        rows=s.scalars(select(Portfolio).order_by(Portfolio.name)).all()
        return rows

@router.post("/api/v1/admin/portfolios",response_model=AdminPortfolioResponse)
def admin_create_portfolio(request:Request,x:PortfolioCreateIn,admin=Depends(current_admin)):
    with Session(engine) as s:
        if s.scalar(select(Portfolio).where(Portfolio.slug==x.slug)):
            raise HTTPException(409,"Portfolio slug already exists")
        p=Portfolio(name=x.name,slug=x.slug,category=x.category,objective=x.objective,risk_level=x.risk_level,minimum_investment=x.minimum_investment,management_fee=x.management_fee,performance_fee=x.performance_fee,benchmark=x.benchmark,base_currency=x.base_currency.upper(),liquidity_terms=x.liquidity_terms,status=x.status)
        s.add(p); s.flush()
        if x.primary_allocation>0:
            s.add(PortfolioAllocation(portfolio_id=p.id,asset_class="Primary Allocation",target_weight=x.primary_allocation))
        s.add(PortfolioPerformance(portfolio_id=p.id,nav=Decimal("100"),daily_return=Decimal("0"),monthly_return=Decimal("0"),ytd_return=Decimal("0")))
        _admin_audit(s,admin,"ADMIN_PORTFOLIO_CREATED","Portfolio",p.id,request)
        s.commit()
        return p

@router.patch("/api/v1/admin/portfolios/{portfolio_id}",response_model=AdminPortfolioResponse)
def admin_update_portfolio(request:Request,portfolio_id:UUID,x:PortfolioUpdateIn,admin=Depends(current_admin)):
    with Session(engine) as s:
        p=s.get(Portfolio,portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        changes=x.model_dump(exclude_unset=True)
        if "base_currency" in changes and changes["base_currency"]: changes["base_currency"]=changes["base_currency"].upper()
        for k,v in changes.items(): setattr(p,k,v)
        _admin_audit(s,admin,"ADMIN_PORTFOLIO_UPDATED","Portfolio",p.id,request)
        s.commit()
        return p

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
            p=Portfolio(name=name,slug=slug,category=cat,objective=obj,risk_level=risk,minimum_investment=Decimal("1000"),management_fee=Decimal(str(fee)),cost_basis_method="AVERAGE_COST",benchmark="Internal blended benchmark",liquidity_terms="Daily")
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

@router.post("/api/v1/admin/orders/{order_id}/executions")
def execute_order(request: Request,order_id:UUID,x:ExecutionIn,c=Depends(current_user)):
    require_staff(c)
    from app.services.execution import apply_execution
    with Session(engine) as s:
        o=s.get(InvestmentOrder,order_id)
        if not o: raise HTTPException(404,"Order not found")
        if o.status in ("CANCELLED","FILLED"): raise HTTPException(400,"Order cannot receive another execution")
        existing=s.scalar(select(ExecutionFill).where(ExecutionFill.execution_id==x.execution_id))
        if existing:
            if existing.order_id!=o.id: raise HTTPException(409,"Execution ID is already assigned to another order")
            return {"executionId":existing.execution_id,"orderId":o.id,"status":o.status,"quantity":existing.quantity,"price":existing.price,"fees":existing.fees,"replayed":True}
        try:
            fill=apply_execution(s,o,x.execution_id,x.quantity,x.price,x.fees)
            audit(s,c,"ORDER_EXECUTED","ExecutionFill",fill.id,request=request)
            s.commit()
            return {"executionId":fill.execution_id,"orderId":o.id,"status":o.status,"quantity":fill.quantity,"price":fill.price,"fees":fill.fees,"replayed":False}
        except ValueError as e:
            s.rollback()
            raise HTTPException(400,str(e))
    
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
    raise HTTPException(410,"Direct single-line ledger creation is disabled. Use a journalized accounting operation so every transaction remains balanced.")

@router.post("/api/v1/admin/valuations/{account_id}")
def create_valuation(request: Request,account_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        account=s.get(InvestmentAccount,account_id)
        if not account: raise HTTPException(404,"Investment account not found")
        positions=s.scalars(select(PortfolioPosition).where(PortfolioPosition.account_id==account_id,PortfolioPosition.quantity>0)).all()
        missing_prices=[p.id for p in positions if p.market_price<=0]
        if missing_prices: raise HTTPException(409,"Valuation blocked: one or more open positions have no positive market price")
        market=sum((p.quantity*p.market_price for p in positions),Decimal("0"))
        rows=s.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_id,LedgerEntry.ledger_account=="CASH")).all()
        cash=sum((e.amount if e.direction=="DEBIT" else -e.amount for e in rows),Decimal("0"))
        snap=ValuationSnapshot(account_id=account_id,market_value=market,cash_value=cash,nav=market+cash,currency=account.base_currency,price_source="INTERNAL_POSITION_PRICES")
        s.add(snap); s.flush(); audit(s,c,"VALUATION_SNAPSHOT_CREATED","ValuationSnapshot",snap.id,request=request); s.commit()
        return {"id":snap.id,"accountId":account_id,"asOf":snap.as_of,"cashValue":snap.cash_value,"marketValue":snap.market_value,"nav":snap.nav,"currency":snap.currency,"priceSource":snap.price_source}

@router.get("/api/v1/admin/reconciliation/{account_id}")
def reconcile(account_id:UUID,c=Depends(current_user)):
    require_staff(c)
    from app.services.reconciliation import reconcile_account
    with Session(engine) as s:
        if not s.get(InvestmentAccount,account_id): raise HTTPException(404,"Investment account not found")
        return reconcile_account(s,account_id)

@router.get("/api/v1/admin/ledger/{account_id}")
def account_ledger(account_id:UUID,c=Depends(current_user)):
    require_staff(c)
    with Session(engine) as s:
        rows=list(s.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_id).order_by(LedgerEntry.created_at)).all())
        balance=sum((x.amount if x.direction=="CREDIT" else -x.amount) for x in rows)
        return {"accountId":account_id,"balance":balance,"entries":rows}


