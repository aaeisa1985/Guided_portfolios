from uuid import UUID
from pydantic import BaseModel
class SuitabilityIn(BaseModel): portfolio_id:UUID
