from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import engine
from app.core.security import current_user
from app.models import (
    AuditLog, CorporateAction, CorporateActionEvent, Customer, Instrument,
    Portfolio, PortfolioAllocation, PortfolioHolding, PortfolioPerformance,
    PortfolioDocument, PortfolioVersion
)
from app.services.audit import audit
from app.services.corporate_actions import process_corporate_action, approve_corporate_action
from app.schemas import (
    ManagerPortfolioCreateIn, ManagerPortfolioUpdateIn, ManagerCompositionIn,
    ManagerInstrumentCreateIn, ManagerDocumentCreateIn, ManagerPerformanceIn, ManagerVersionIn
)
from app.services.storage import create_upload, create_download

router = APIRouter(tags=["Manager"])

def require_manager(c):
    if c.role != "MANAGER":
        raise HTTPException(403, "Manager role required")
    return c

def _portfolio_or_404(s, portfolio_id):
    p = s.get(Portfolio, portfolio_id)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    return p

def _validate_weights(composition: ManagerCompositionIn):
    groups = {"ASSET": [], "SECTOR": [], "GEO": []}
    for item in composition.allocations:
        groups[item.dimension].append(item.target_weight)
        if item.max_weight < item.min_weight:
            raise HTTPException(400, f"Invalid allocation range for {item.label}")
    holdings_total = sum((x.target_weight for x in composition.holdings), Decimal("0"))
    for dim, values in groups.items():
        if values:
            total = sum(values, Decimal("0"))
            if abs(total - Decimal("100")) > Decimal("0.01"):
                raise HTTPException(400, f"{dim} allocation must total 100%; current total={total}")
    if composition.holdings:
        if abs(holdings_total - Decimal("100")) > Decimal("0.01"):
            raise HTTPException(400, f"HOLDINGS allocation must total 100%; current total={holdings_total}")

def _replace_composition(s, portfolio_id, composition: ManagerCompositionIn):
    _validate_weights(composition)
    s.query(PortfolioAllocation).filter(PortfolioAllocation.portfolio_id == portfolio_id).delete(synchronize_session=False)
    s.query(PortfolioHolding).filter(PortfolioHolding.portfolio_id == portfolio_id).delete(synchronize_session=False)

    for item in composition.allocations:
        s.add(PortfolioAllocation(
            portfolio_id=portfolio_id,
            asset_class=f"{item.dimension}:{item.label}",
            target_weight=item.target_weight,
            min_weight=item.min_weight,
            max_weight=item.max_weight,
        ))

    for h in composition.holdings:
        if h.instrument_id and not s.get(Instrument, h.instrument_id):
            raise HTTPException(404, f"Instrument not found: {h.instrument_id}")
        s.add(PortfolioHolding(
            portfolio_id=portfolio_id,
            instrument_name=h.instrument_name,
            instrument_type=h.instrument_type,
            ticker=h.ticker,
            instrument_id=h.instrument_id,
            target_weight=h.target_weight,
        ))

def _composition(s, portfolio_id):
    rows = s.scalars(select(PortfolioAllocation).where(PortfolioAllocation.portfolio_id == portfolio_id)).all()
    alloc = {"ASSET": [], "SECTOR": [], "GEO": []}
    for r in rows:
        if ":" in r.asset_class:
            dim, label = r.asset_class.split(":", 1)
            dim = dim.upper()
        else:
            dim, label = "ASSET", r.asset_class
        alloc.setdefault(dim, []).append({
            "id": r.id, "dimension": dim, "label": label,
            "targetWeight": r.target_weight, "minWeight": r.min_weight, "maxWeight": r.max_weight,
        })
    holdings = s.scalars(select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)).all()
    return {
        "assets": alloc.get("ASSET", []),
        "sectors": alloc.get("SECTOR", []),
        "geography": alloc.get("GEO", []),
        "holdings": [{
            "id": h.id, "instrumentId": h.instrument_id, "instrumentName": h.instrument_name,
            "instrumentType": h.instrument_type, "ticker": h.ticker, "targetWeight": h.target_weight
        } for h in holdings],
    }

@router.get("/api/v1/manager/auth/me")
def manager_me(c=Depends(current_user)):
    require_manager(c)
    return {"id": c.id, "customerId": c.customer_id, "name": c.full_name, "email": c.email, "role": c.role}

@router.get("/api/v1/manager/overview")
def manager_overview(c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        total = s.scalar(select(func.count()).select_from(Portfolio)) or 0
        active = s.scalar(select(func.count()).select_from(Portfolio).where(Portfolio.status == "ACTIVE")) or 0
        draft = s.scalar(select(func.count()).select_from(Portfolio).where(Portfolio.status == "DRAFT")) or 0
        instruments = s.scalar(select(func.count()).select_from(Instrument)) or 0
        actions = s.scalar(select(func.count()).select_from(CorporateAction)) or 0
        pending_actions = s.scalar(select(func.count()).select_from(CorporateAction).where(CorporateAction.status.in_(["DRAFT","APPROVED","PROCESSING"]))) or 0
        documents = s.scalar(select(func.count()).select_from(PortfolioDocument)) or 0
        return {"portfolios": total, "activePortfolios": active, "draftPortfolios": draft,
                "instruments": instruments, "corporateActions": actions,
                "pendingCorporateActions": pending_actions, "documents": documents}

@router.get("/api/v1/manager/portfolios")
def manager_portfolios(c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        rows = s.scalars(select(Portfolio).order_by(Portfolio.name)).all()
        return [{
            "id": p.id, "name": p.name, "slug": p.slug, "vehicleType": p.vehicle_type,
            "category": p.category, "objective": p.objective, "riskLevel": p.risk_level,
            "minimumInvestment": p.minimum_investment, "managementFee": p.management_fee,
            "performanceFee": p.performance_fee, "benchmark": p.benchmark,
            "baseCurrency": p.base_currency, "liquidityTerms": p.liquidity_terms, "status": p.status,
            "strategy": p.strategy, "investmentStyle": p.investment_style,
            "shariahStatus": p.shariah_status, "distributionPolicy": p.distribution_policy,
            "reviewFrequency": p.review_frequency, "targetHorizonYears": p.target_horizon_years,
            "inceptionDate": p.inception_date
        } for p in rows]

@router.post("/api/v1/manager/portfolios")
def manager_create_portfolio(request: Request, x: ManagerPortfolioCreateIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        if s.scalar(select(Portfolio).where(Portfolio.slug == x.slug)):
            raise HTTPException(409, "Portfolio slug already exists")
        p = Portfolio(
            name=x.name, slug=x.slug, vehicle_type=x.vehicle_type, category=x.category,
            objective=x.objective, strategy=x.strategy, investment_style=x.investment_style,
            shariah_status=x.shariah_status, distribution_policy=x.distribution_policy,
            review_frequency=x.review_frequency, target_horizon_years=x.target_horizon_years,
            inception_date=datetime.fromisoformat(x.inception_date.replace("Z","+00:00")) if x.inception_date else None,
            risk_level=x.risk_level, minimum_investment=x.minimum_investment,
            management_fee=x.management_fee, performance_fee=x.performance_fee,
            cost_basis_method=x.cost_basis_method, benchmark=x.benchmark,
            base_currency=x.base_currency.upper(), liquidity_terms=x.liquidity_terms, status="DRAFT"
        )
        s.add(p); s.flush()
        _replace_composition(s, p.id, x.composition)
        s.add(PortfolioPerformance(portfolio_id=p.id, nav=Decimal("100")))
        audit(s, c, "MANAGER_PORTFOLIO_CREATED", "Portfolio", p.id, request=request)
        s.commit()
        return {"id": p.id, "status": p.status}

@router.get("/api/v1/manager/portfolios/{portfolio_id}")
def manager_portfolio_detail(portfolio_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        p = _portfolio_or_404(s, portfolio_id)
        perf = s.scalars(select(PortfolioPerformance).where(PortfolioPerformance.portfolio_id == p.id).order_by(PortfolioPerformance.date.desc()).limit(60)).all()
        docs = s.scalars(select(PortfolioDocument).where(PortfolioDocument.portfolio_id == p.id).order_by(PortfolioDocument.published_at.desc())).all()
        return {
            "portfolio": {
                "id": p.id, "name": p.name, "slug": p.slug, "vehicleType": p.vehicle_type,
                "category": p.category, "objective": p.objective, "riskLevel": p.risk_level,
                "minimumInvestment": p.minimum_investment, "managementFee": p.management_fee,
                "performanceFee": p.performance_fee, "costBasisMethod": p.cost_basis_method,
                "strategy": p.strategy, "investmentStyle": p.investment_style,
                "shariahStatus": p.shariah_status, "distributionPolicy": p.distribution_policy,
                "reviewFrequency": p.review_frequency, "targetHorizonYears": p.target_horizon_years,
                "inceptionDate": p.inception_date, "benchmark": p.benchmark, "baseCurrency": p.base_currency,
                "liquidityTerms": p.liquidity_terms, "status": p.status
            },
            "composition": _composition(s, p.id),
            "performance": [{
                "id": x.id, "date": x.date, "nav": x.nav, "dailyReturn": x.daily_return,
                "monthlyReturn": x.monthly_return, "ytdReturn": x.ytd_return
            } for x in reversed(perf)],
            "documents": [{
                "id": d.id, "documentType": d.document_type, "fileUrl": d.file_url,
                "version": d.version, "publishedAt": d.published_at
            } for d in docs],
        }

@router.patch("/api/v1/manager/portfolios/{portfolio_id}")
def manager_update_portfolio(request: Request, portfolio_id: UUID, x: ManagerPortfolioUpdateIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        p = _portfolio_or_404(s, portfolio_id)
        changes = x.model_dump(exclude_unset=True)
        if "base_currency" in changes and changes["base_currency"]:
            changes["base_currency"] = changes["base_currency"].upper()
        if "inception_date" in changes and changes["inception_date"]:
            changes["inception_date"] = datetime.fromisoformat(changes["inception_date"].replace("Z","+00:00"))
        requested_status = changes.get("status")
        composition = changes.pop("composition", None)
        if requested_status == "ACTIVE":
            raise HTTPException(400, "Use the controlled publish workflow after version approval")
        for k, v in changes.items():
            setattr(p, k, v)
        if composition is not None:
            _replace_composition(s, p.id, composition)
        audit(s, c, "MANAGER_PORTFOLIO_UPDATED", "Portfolio", p.id, request=request)
        s.commit()
        return {"id": p.id, "status": p.status}

@router.put("/api/v1/manager/portfolios/{portfolio_id}/composition")
def manager_update_composition(request: Request, portfolio_id: UUID, x: ManagerCompositionIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        p = _portfolio_or_404(s, portfolio_id)
        _replace_composition(s, p.id, x)
        audit(s, c, "MANAGER_PORTFOLIO_COMPOSITION_UPDATED", "Portfolio", p.id, request=request)
        s.commit()
        return {"id": p.id, "composition": _composition(s, p.id)}

@router.post("/api/v1/manager/portfolios/{portfolio_id}/performance")
def manager_add_performance(request: Request, portfolio_id: UUID, x: ManagerPerformanceIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        _portfolio_or_404(s, portfolio_id)
        obs = PortfolioPerformance(
            portfolio_id=portfolio_id, nav=x.nav, daily_return=x.daily_return,
            monthly_return=x.monthly_return, ytd_return=x.ytd_return
        )
        s.add(obs); s.flush()
        audit(s, c, "MANAGER_NAV_OBSERVATION_CREATED", "PortfolioPerformance", obs.id, request=request)
        s.commit()
        return {"id": obs.id, "date": obs.date}

@router.get("/api/v1/manager/instruments")
def manager_instruments(status: Optional[str] = Query(None), q: Optional[str] = Query(None), c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        stmt = select(Instrument).order_by(Instrument.name)
        if status:
            stmt = stmt.where(Instrument.status == status.upper())
        if q:
            term = f"%{q.strip()}%"
            stmt = stmt.where(Instrument.name.ilike(term) | Instrument.symbol.ilike(term) | Instrument.isin.ilike(term))
        rows = s.scalars(stmt.limit(500)).all()
        return [{
            "id": x.id, "symbol": x.symbol, "name": x.name, "instrumentType": x.instrument_type,
            "assetClass": x.asset_class, "currency": x.currency, "isin": x.isin, "status": x.status
        } for x in rows]

@router.post("/api/v1/manager/instruments")
def manager_create_instrument(request: Request, x: ManagerInstrumentCreateIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        if x.symbol and s.scalar(select(Instrument).where(Instrument.symbol == x.symbol)):
            raise HTTPException(409, "Instrument symbol already exists")
        if x.isin and s.scalar(select(Instrument).where(Instrument.isin == x.isin)):
            raise HTTPException(409, "Instrument ISIN already exists")
        i = Instrument(
            symbol=x.symbol, name=x.name, instrument_type=x.instrument_type,
            asset_class=x.asset_class, currency=x.currency.upper(), isin=x.isin, status=x.status
        )
        s.add(i); s.flush()
        audit(s, c, "MANAGER_INSTRUMENT_CREATED", "Instrument", i.id, request=request)
        s.commit()
        return {"id": i.id, "name": i.name, "symbol": i.symbol}

@router.patch("/api/v1/manager/instruments/{instrument_id}")
def manager_update_instrument(request: Request, instrument_id: UUID, x: ManagerInstrumentCreateIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        i = s.get(Instrument, instrument_id)
        if not i: raise HTTPException(404, "Instrument not found")
        if x.symbol and s.scalar(select(Instrument).where(Instrument.symbol == x.symbol, Instrument.id != i.id)):
            raise HTTPException(409, "Instrument symbol already exists")
        if x.isin and s.scalar(select(Instrument).where(Instrument.isin == x.isin, Instrument.id != i.id)):
            raise HTTPException(409, "Instrument ISIN already exists")
        for k,v in x.model_dump().items():
            setattr(i, k, v.upper() if k == "currency" and v else v)
        audit(s, c, "MANAGER_INSTRUMENT_UPDATED", "Instrument", i.id, request=request)
        s.commit()
        return {"id": i.id, "status": i.status}

@router.get("/api/v1/manager/portfolios/{portfolio_id}/documents")
def manager_documents(portfolio_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        _portfolio_or_404(s, portfolio_id)
        rows = s.scalars(select(PortfolioDocument).where(PortfolioDocument.portfolio_id == portfolio_id).order_by(PortfolioDocument.published_at.desc())).all()
        return [{
            "id": d.id, "documentType": d.document_type, "fileUrl": d.file_url,
            "version": d.version, "publishedAt": d.published_at
        } for d in rows]

@router.post("/api/v1/manager/portfolios/{portfolio_id}/documents")
def manager_add_document(request: Request, portfolio_id: UUID, x: ManagerDocumentCreateIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        _portfolio_or_404(s, portfolio_id)
        d = PortfolioDocument(
            portfolio_id=portfolio_id, document_type=x.document_type.upper(),
            file_url=x.file_url, version=x.version,
            status="PUBLISHED" if x.published else "DRAFT",
            published_at=datetime.now(timezone.utc)
        )
        s.add(d); s.flush()
        audit(s, c, "MANAGER_DOCUMENT_PUBLISHED", "PortfolioDocument", d.id, request=request)
        s.commit()
        return {"id": d.id, "documentType": d.document_type, "version": d.version}


@router.post("/api/v1/manager/portfolios/{portfolio_id}/documents/upload-url")
def manager_document_upload_url(
    request: Request,
    portfolio_id: UUID,
    filename: str = Query(..., min_length=1, max_length=200),
    content_type: str = Query("application/pdf"),
    c=Depends(current_user)
):
    require_manager(c)
    with Session(engine) as s:
        _portfolio_or_404(s, portfolio_id)
    try:
        return create_upload(filename, content_type, portfolio_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))

@router.get("/api/v1/manager/documents/{document_id}/signed-url")
def manager_document_signed_url(document_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        d=s.get(PortfolioDocument,document_id)
        if not d: raise HTTPException(404,"Document not found")
        path=d.file_url
    try:
        return {"signedUrl":create_download(path)}
    except RuntimeError as e:
        raise HTTPException(503,str(e))

@router.delete("/api/v1/manager/documents/{document_id}")
def manager_delete_document(request: Request, document_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        d = s.get(PortfolioDocument, document_id)
        if not d: raise HTTPException(404, "Document not found")
        s.delete(d)
        audit(s, c, "MANAGER_DOCUMENT_DELETED", "PortfolioDocument", document_id, request=request)
        s.commit()
        return {"deleted": True}

@router.get("/api/v1/manager/versions")
def manager_versions(portfolio_id: Optional[UUID] = Query(None), c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        stmt = select(PortfolioVersion).order_by(PortfolioVersion.created_at.desc())
        if portfolio_id:
            stmt = stmt.where(PortfolioVersion.portfolio_id == portfolio_id)
        rows = s.scalars(stmt.limit(200)).all()
        return [{
            "id": v.id, "portfolioId": v.portfolio_id, "versionNumber": v.version_number,
            "status": v.status, "effectiveAt": v.effective_at, "createdAt": v.created_at,
            "approvedBy": v.approved_by, "createdBy": v.created_by, "notes": v.notes
        } for v in rows]

@router.post("/api/v1/manager/portfolios/{portfolio_id}/versions")
def manager_create_version(request: Request, portfolio_id: UUID, payload: ManagerVersionIn, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        _portfolio_or_404(s, portfolio_id)
        n = (s.scalar(select(PortfolioVersion.version_number).where(PortfolioVersion.portfolio_id == portfolio_id).order_by(PortfolioVersion.version_number.desc())) or 0) + 1
        v = PortfolioVersion(portfolio_id=portfolio_id, version_number=n, status="DRAFT", created_by=c.id, notes=payload.notes)
        s.add(v); s.flush()
        audit(s, c, "MANAGER_PORTFOLIO_VERSION_CREATED", "PortfolioVersion", v.id, request=request)
        s.commit()
        return {"id": v.id, "versionNumber": n, "status": v.status}

@router.post("/api/v1/manager/portfolios/{portfolio_id}/versions/{version_id}/approve")
def manager_approve_version(request: Request, portfolio_id: UUID, version_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        v = s.scalar(select(PortfolioVersion).where(PortfolioVersion.id == version_id, PortfolioVersion.portfolio_id == portfolio_id))
        if not v: raise HTTPException(404, "Portfolio version not found")
        if v.created_by == c.id: raise HTTPException(400, "Maker/checker control: creator cannot approve the same version")
        v.status = "ACTIVE"; v.effective_at = datetime.now(timezone.utc); v.approved_by = c.id
        audit(s, c, "MANAGER_PORTFOLIO_VERSION_APPROVED", "PortfolioVersion", v.id, request=request)
        s.commit()
        return {"id": v.id, "status": v.status}

@router.get("/api/v1/manager/corporate-actions")
def manager_corporate_actions(status: Optional[str] = Query(None), c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        stmt = select(CorporateAction).order_by(CorporateAction.ex_date.desc())
        if status:
            stmt = stmt.where(CorporateAction.status == status.upper())
        rows = s.scalars(stmt.limit(500)).all()
        return [{
            "id": a.id, "instrumentId": a.instrument_id, "actionType": a.action_type, "status": a.status,
            "exDate": a.ex_date, "recordDate": a.record_date, "paymentDate": a.payment_date,
            "effectiveDate": a.effective_date, "ratioNumerator": a.ratio_numerator,
            "ratioDenominator": a.ratio_denominator, "dividendPerShare": a.dividend_per_share,
            "subscriptionPrice": a.subscription_price, "replacementInstrumentId": a.replacement_instrument_id,
            "exchangeRatio": a.exchange_ratio, "description": a.description, "failureReason": a.failure_reason,
            "createdBy": a.created_by, "approvedBy": a.approved_by, "executedAt": a.executed_at
        } for a in rows]

@router.post("/api/v1/manager/corporate-actions")
def manager_create_corporate_action(request: Request, payload: dict, c=Depends(current_user)):
    require_manager(c)
    from app.api.corporate_actions import CorporateActionIn
    try:
        x = CorporateActionIn.model_validate(payload)
    except Exception as e:
        raise HTTPException(422, str(e))
    with Session(engine) as s:
        if not s.get(Instrument, x.instrument_id): raise HTTPException(404, "Instrument not found")
        ca = CorporateAction(**x.model_dump(), created_by=c.id)
        s.add(ca); s.flush()
        audit(s, c, "MANAGER_CORPORATE_ACTION_CREATED", "CorporateAction", ca.id, request=request)
        s.commit()
        return {"id": ca.id, "status": ca.status}

@router.post("/api/v1/manager/corporate-actions/{action_id}/approve")
def manager_approve_corporate_action(action_id: UUID, request: Request, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        ca = s.get(CorporateAction, action_id)
        if not ca: raise HTTPException(404, "Corporate action not found")
        try:
            approve_corporate_action(s, ca, c)
            audit(s, c, "MANAGER_CORPORATE_ACTION_APPROVED", "CorporateAction", ca.id, request=request)
            s.commit()
        except ValueError as e:
            s.rollback()
            raise HTTPException(400, str(e))
        return {"id": ca.id, "status": ca.status}

@router.post("/api/v1/manager/corporate-actions/{action_id}/execute")
def manager_execute_corporate_action(action_id: UUID, request: Request, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        ca = s.get(CorporateAction, action_id)
        if not ca: raise HTTPException(404, "Corporate action not found")
        try:
            events = process_corporate_action(s, ca)
            audit(s, c, "MANAGER_CORPORATE_ACTION_EXECUTED", "CorporateAction", ca.id, request=request)
            s.commit()
        except ValueError as e:
            s.rollback()
            raise HTTPException(400, str(e))
        return {"id": ca.id, "status": ca.status, "eventsProcessed": len(events), "executedAt": ca.executed_at}

@router.get("/api/v1/manager/corporate-actions/{action_id}/events")
def manager_corporate_action_events(action_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        if not s.get(CorporateAction, action_id): raise HTTPException(404, "Corporate action not found")
        return [{
            "id": e.id, "positionId": e.position_id, "quantityBefore": e.quantity_before,
            "quantityAfter": e.quantity_after, "cashImpact": e.cash_impact,
            "incomeRecognized": e.income_recognized, "cashInLieu": e.cash_in_lieu
        } for e in s.scalars(select(CorporateActionEvent).where(CorporateActionEvent.corporate_action_id == action_id)).all()]

@router.get("/api/v1/manager/audit")
def manager_audit(limit: int = Query(200, le=500), c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        return list(s.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all())


@router.get("/api/v1/manager/portfolios/{portfolio_id}/readiness")
def manager_portfolio_readiness(portfolio_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        p = _portfolio_or_404(s, portfolio_id)
        comp = _composition(s, p.id)
        active_version = s.scalar(select(PortfolioVersion).where(
            PortfolioVersion.portfolio_id == p.id, PortfolioVersion.status == "ACTIVE"
        ).order_by(PortfolioVersion.version_number.desc()))
        fact_sheet = s.scalar(select(PortfolioDocument).where(
            PortfolioDocument.portfolio_id == p.id,
            PortfolioDocument.document_type == "FACT_SHEET",
            PortfolioDocument.status == "PUBLISHED"
        ).order_by(PortfolioDocument.published_at.desc()))
        checks = {
            "strategy": bool((p.strategy or "").strip()),
            "assetAllocation": not comp["assets"] or abs(sum((Decimal(str(x["targetWeight"])) for x in comp["assets"]), Decimal("0")) - Decimal("100")) <= Decimal("0.01"),
            "holdings": bool(comp["holdings"]) and abs(sum((Decimal(str(x["targetWeight"])) for x in comp["holdings"]), Decimal("0")) - Decimal("100")) <= Decimal("0.01"),
            "activeVersion": bool(active_version),
            "factSheet": bool(fact_sheet),
        }
        return {"portfolioId": p.id, "status": p.status, "checks": checks, "ready": all(checks.values()),
                "activeVersionId": active_version.id if active_version else None,
                "factSheetId": fact_sheet.id if fact_sheet else None}

@router.post("/api/v1/manager/portfolios/{portfolio_id}/publish")
def manager_publish_portfolio(request: Request, portfolio_id: UUID, c=Depends(current_user)):
    require_manager(c)
    with Session(engine) as s:
        p = _portfolio_or_404(s, portfolio_id)
        comp = _composition(s, p.id)
        active_version = s.scalar(select(PortfolioVersion).where(
            PortfolioVersion.portfolio_id == p.id, PortfolioVersion.status == "ACTIVE"
        ).order_by(PortfolioVersion.version_number.desc()))
        fact_sheet = s.scalar(select(PortfolioDocument).where(
            PortfolioDocument.portfolio_id == p.id,
            PortfolioDocument.document_type == "FACT_SHEET",
            PortfolioDocument.status == "PUBLISHED"
        ).order_by(PortfolioDocument.published_at.desc()))
        checks = [
            bool((p.strategy or "").strip()),
            bool(comp["holdings"]) and abs(sum((Decimal(str(x["targetWeight"])) for x in comp["holdings"]), Decimal("0")) - Decimal("100")) <= Decimal("0.01"),
            not comp["assets"] or abs(sum((Decimal(str(x["targetWeight"])) for x in comp["assets"]), Decimal("0")) - Decimal("100")) <= Decimal("0.01"),
            bool(active_version),
            bool(fact_sheet),
        ]
        if not all(checks):
            raise HTTPException(409, "Portfolio is not publication-ready. Complete strategy, 100% holdings/assets, approved version and FACT_SHEET first.")
        p.status = "ACTIVE"
        audit(s, c, "MANAGER_PORTFOLIO_PUBLISHED", "Portfolio", p.id, request=request)
        s.commit()
        return {"id": p.id, "status": p.status}