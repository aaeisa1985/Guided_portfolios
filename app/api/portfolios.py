from typing import Optional
from uuid import UUID
from fastapi import Query,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models import Portfolio,PortfolioAllocation,PortfolioHolding,PortfolioPerformance,PortfolioDocument
from app.schemas import PortfolioOut
from fastapi import APIRouter
router=APIRouter()

@router.get("/api/v1/portfolios",response_model=list[PortfolioOut])
def portfolios(category:Optional[str]=Query(None),risk_level:Optional[int]=None):
    with Session(engine) as s:
        q=select(Portfolio).where(Portfolio.status=="ACTIVE")
        if category:q=q.where(Portfolio.category==category)
        if risk_level is not None:q=q.where(Portfolio.risk_level==risk_level)
        return list(s.scalars(q).all())

@router.get("/api/v1/portfolios/{portfolio_id}")
def portfolio_detail(portfolio_id:UUID):
    with Session(engine) as s:
        p=s.get(Portfolio,portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        a=list(s.scalars(select(PortfolioAllocation).where(PortfolioAllocation.portfolio_id==p.id)).all())
        h=list(s.scalars(select(PortfolioHolding).where(PortfolioHolding.portfolio_id==p.id)).all())
        perf=list(s.scalars(select(PortfolioPerformance).where(PortfolioPerformance.portfolio_id==p.id).order_by(PortfolioPerformance.date.desc()).limit(30)).all())
        docs=list(s.scalars(select(PortfolioDocument).where(PortfolioDocument.portfolio_id==p.id)).all())
        return {"portfolio":PortfolioOut.model_validate(p),"allocations":a,"holdings":h,"performance":perf,"documents":docs}
