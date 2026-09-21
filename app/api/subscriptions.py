import json
from datetime import datetime,timezone
from typing import Optional
from uuid import UUID
from fastapi import Depends,Header,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.security import current_user
from app.models import Portfolio,PortfolioSubscription,PortfolioVersion,InvestmentAccount,RiskAssessment,SuitabilityAssessment,SubscriptionEvent,IdempotencyKey
from app.schemas import SubscriptionIn
from app.services.audit import audit
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/subscriptions")
def subscribe(request:Request,x:SubscriptionIn,c=Depends(current_user),x_idempotency_key:Optional[str]=Header(None,alias="X-Idempotency-Key")):
    with Session(engine) as s:
        if x_idempotency_key:
            prior=s.scalar(select(IdempotencyKey).where(IdempotencyKey.customer_id==c.id,IdempotencyKey.key==x_idempotency_key,IdempotencyKey.endpoint=="POST:/api/v1/subscriptions"))
            if prior: return json.loads(prior.response_body)
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
        s.add(SubscriptionEvent(subscription_id=sub.id,event_type="CREATED"))
        s.add(SubscriptionEvent(subscription_id=sub.id,event_type="SUITABILITY_CHECKED"))
        audit(s,c,"SUBSCRIPTION_CREATED","PortfolioSubscription",sub.id,request=request)
        response={"subscriptionId":sub.id,"status":sub.status,"portfolioId":sub.portfolio_id,"portfolioVersionId":sub.portfolio_version_id,"amount":sub.subscription_amount,"currency":p.base_currency,"createdAt":sub.created_at}
        if x_idempotency_key:
            s.add(IdempotencyKey(customer_id=c.id,key=x_idempotency_key,endpoint="POST:/api/v1/subscriptions",response_status=200,response_body=json.dumps(response,default=str)))
        s.commit()
        return response

@router.get("/api/v1/subscriptions")
def subscriptions(c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        if not a:return []
        rows=list(s.scalars(select(PortfolioSubscription).where(PortfolioSubscription.account_id==a.id).order_by(PortfolioSubscription.created_at.desc())).all())
        return [{"id":x.id,"portfolio_id":x.portfolio_id,"portfolio_name":(s.get(Portfolio,x.portfolio_id).name if s.get(Portfolio,x.portfolio_id) else "Portfolio"),"subscription_amount":x.subscription_amount,"units":x.units,"status":x.status,"created_at":x.created_at,"currency":(s.get(Portfolio,x.portfolio_id).base_currency if s.get(Portfolio,x.portfolio_id) else "AED")} for x in rows]

@router.get("/api/v1/subscriptions/{subscription_id}")
def subscription(subscription_id:UUID,c=Depends(current_user)):
    with Session(engine) as s:
        a=s.scalar(select(InvestmentAccount).where(InvestmentAccount.customer_id==c.id))
        sub=s.scalar(select(PortfolioSubscription).where(PortfolioSubscription.id==subscription_id,PortfolioSubscription.account_id==a.id))
        if not sub: raise HTTPException(404,"Subscription not found")
        events=list(s.scalars(select(SubscriptionEvent).where(SubscriptionEvent.subscription_id==sub.id).order_by(SubscriptionEvent.created_at)).all())
        return {"subscription":sub,"events":events}
