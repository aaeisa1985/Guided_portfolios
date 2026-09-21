from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class SimulatorIn(BaseModel):
    portfolio_id:UUID; amount:Decimal=Field(gt=0); years:int=Field(ge=1,le=50)
