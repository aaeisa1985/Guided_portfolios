from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class SubscriptionIn(BaseModel): portfolio_id:UUID; amount:Decimal=Field(gt=0)
