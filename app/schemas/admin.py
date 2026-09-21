from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field

class AdminLoginIn(BaseModel):
    username:str=Field(min_length=1,max_length=120)
    password:str=Field(min_length=1,max_length=256)

class PortfolioCreateIn(BaseModel):
    name:str=Field(min_length=2,max_length=200)
    slug:str=Field(min_length=2,max_length=100,pattern=r"^[a-z0-9-]+$")
    category:str=Field(min_length=2,max_length=60)
    objective:str=Field(min_length=2)
    risk_level:int=Field(ge=1,le=5)
    minimum_investment:Decimal=Field(ge=0)
    management_fee:Decimal=Field(ge=0)
    performance_fee:Decimal=Field(ge=0)
    benchmark:str|None=None
    base_currency:str=Field(default="AED",min_length=3,max_length=3)
    liquidity_terms:str=Field(default="Daily",min_length=1,max_length=100)
    status:str=Field(default="ACTIVE",pattern=r"^(ACTIVE|DRAFT|ARCHIVED)$")
    primary_allocation:Decimal=Field(default=Decimal("100"),ge=0,le=100)

class PortfolioUpdateIn(BaseModel):
    name:str|None=None
    category:str|None=None
    objective:str|None=None
    risk_level:int|None=Field(default=None,ge=1,le=5)
    minimum_investment:Decimal|None=Field(default=None,ge=0)
    management_fee:Decimal|None=Field(default=None,ge=0)
    performance_fee:Decimal|None=Field(default=None,ge=0)
    benchmark:str|None=None
    base_currency:str|None=Field(default=None,min_length=3,max_length=3)
    liquidity_terms:str|None=None
    status:str|None=Field(default=None,pattern=r"^(ACTIVE|DRAFT|ARCHIVED)$")

class AdminUserUpdateIn(BaseModel):
    full_name:str|None=None
    mobile:str|None=None
    investor_type:str|None=None
    kyc_status:str|None=None
    aml_status:str|None=None
    role:str|None=Field(default=None,pattern=r"^(INVESTOR|MANAGER|ADMIN)$")

class AdminPortfolioResponse(BaseModel):
    id:UUID; name:str; slug:str; category:str; risk_level:int; minimum_investment:Decimal
    management_fee:Decimal; performance_fee:Decimal; base_currency:str; liquidity_terms:str; status:str
