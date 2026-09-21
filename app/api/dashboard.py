from decimal import Decimal
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import PortfolioSubscription,PortfolioPosition,InvestmentAccount
from fastapi import APIRouter
router=APIRouter()
@router.get("/api/v1/dashboard")
def dashboard(c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        subs=[] if not a else list(s.scalars(select(PortfolioSubscription).where(PortfolioSubscription.account_id==a.id)).all())
        invested=sum((x.subscription_amount for x in subs if x.status in ("ALLOCATED","COMPLETED")),Decimal("0"))
        pending=sum((x.subscription_amount for x in subs if x.status not in ("ALLOCATED","COMPLETED")),Decimal("0"))
        positions=[] if not a else list(s.scalars(select(PortfolioPosition).where(PortfolioPosition.account_id==a.id,PortfolioPosition.quantity>0)).all())
        market_value=sum((p.quantity*p.market_price for p in positions),Decimal("0"))
        unrealized=sum((p.quantity*(p.market_price-p.average_cost) for p in positions),Decimal("0"))
        return {"accountId":None if not a else a.id,"aum":market_value if positions else invested,"marketValue":market_value if positions else invested,"profitLoss":unrealized,"realizedProfitLoss":sum((p.realized_pnl for p in positions),Decimal("0")),"pendingSubscriptions":pending,"portfolioCount":len(subs),"valuationStatus":"POSITION_BASED" if positions else "SUBSCRIPTION_BASED_ESTIMATE"}
