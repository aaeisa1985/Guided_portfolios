from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import PortfolioPosition,Instrument,InvestmentAccount
router=APIRouter(prefix="/api/v1/positions",tags=["positions"])
@router.get("")
def positions(c=Depends(current_user)):
    with Session(engine) as s:
        account=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id,InvestmentAccount.status=="ACTIVE"))
        if not account: return []
        rows=s.scalars(select(PortfolioPosition).where(PortfolioPosition.account_id==account.id).order_by(PortfolioPosition.updated_at.desc())).all()
        result=[]
        for p in rows:
            instrument=s.get(Instrument,p.instrument_id)
            result.append({"id":p.id,"portfolioId":p.portfolio_id,"instrumentId":p.instrument_id,"instrument":instrument.name if instrument else "Instrument","quantity":float(p.quantity),"averageCost":float(p.average_cost),"marketPrice":float(p.market_price),"marketValue":float(p.quantity*p.market_price),"unrealizedPnL":float(p.quantity*(p.market_price-p.average_cost)),"realizedPnL":float(p.realized_pnl),"priceAsOf":p.price_as_of,"priceSource":p.price_source,"currency":p.currency,"updatedAt":p.updated_at})
        return result
