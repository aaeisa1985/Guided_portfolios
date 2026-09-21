from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models import Portfolio
from app.schemas import SimulatorIn
from fastapi import APIRouter
router=APIRouter()

@router.post("/api/v1/simulator")
def simulator(x:SimulatorIn):
    with Session(engine) as s:
        p=s.get(Portfolio,x.portfolio_id)
        if not p: raise HTTPException(404,"Portfolio not found")
        expected={1:0.045,2:0.06,3:0.075,4:0.09,5:0.11}.get(p.risk_level,0.075)
        fee=float(p.management_fee)/100
        net=max(0.0,expected-fee)
        return {"initialInvestment":x.amount,"periodYears":x.years,"expectedAnnualReturn":net,"managementFee":float(p.management_fee),"scenarios":{"conservative":float(x.amount)*(1+max(-.05,net-.04))**x.years,"base":float(x.amount)*(1+net)**x.years,"optimistic":float(x.amount)*(1+net+.04)**x.years},"disclaimer":"Illustrative projection only; not a guarantee or investment recommendation."}
