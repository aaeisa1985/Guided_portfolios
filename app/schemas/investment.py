from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel,Field
class InstrumentIn(BaseModel):
    symbol:Optional[str]=None; name:str; instrument_type:str; asset_class:str; currency:str="AED"; isin:Optional[str]=None
class LedgerEntryIn(BaseModel):
    account_id:UUID; entry_type:str; direction:str; amount:Decimal=Field(gt=0); currency:str="AED"; units:Decimal=Field(default=0,ge=0); description:str=""
class OrderIn(BaseModel):
    account_id:UUID; portfolio_id:UUID; instrument_id:UUID; side:str; quantity:Decimal=Field(gt=0); order_type:str="MARKET"; limit_price:Optional[Decimal]=Field(default=None,gt=0)
