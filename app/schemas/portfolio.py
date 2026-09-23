from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,ConfigDict
class PortfolioOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID; name:str; slug:str; vehicle_type:str; category:str; objective:str; risk_level:int
    minimum_investment:Decimal; management_fee:Decimal; performance_fee:Decimal; benchmark:str|None
    strategy:str; investment_style:str; shariah_status:str; distribution_policy:str
    review_frequency:str; target_horizon_years:int|None; inception_date:object|None
    base_currency:str; liquidity_terms:str; status:str
