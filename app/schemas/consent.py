from uuid import UUID
from pydantic import BaseModel
class ConsentIn(BaseModel):
    portfolio_id:UUID; consent_type:str; consent_text:str; accepted:bool
