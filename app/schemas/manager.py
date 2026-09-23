from decimal import Decimal
from typing import Optional
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, Field

class ManagerAllocationIn(BaseModel):
    dimension: Literal["ASSET","SECTOR","GEO"] = "ASSET"
    label: str = Field(min_length=1, max_length=70)
    target_weight: Decimal = Field(ge=0, le=100)
    min_weight: Decimal = Field(default=0, ge=0, le=100)
    max_weight: Decimal = Field(default=100, ge=0, le=100)

class ManagerHoldingIn(BaseModel):
    instrument_id: Optional[UUID] = None
    instrument_name: str = Field(min_length=1, max_length=200)
    instrument_type: str = Field(default="OTHER", min_length=1, max_length=50)
    ticker: Optional[str] = Field(default=None, max_length=50)
    target_weight: Decimal = Field(ge=0, le=100)

class ManagerCompositionIn(BaseModel):
    allocations: list[ManagerAllocationIn] = Field(default_factory=list)
    holdings: list[ManagerHoldingIn] = Field(default_factory=list)

class ManagerPortfolioCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    vehicle_type: str = Field(default="MODEL_PORTFOLIO", min_length=1, max_length=40)
    category: str = Field(min_length=2, max_length=60)
    objective: str = Field(min_length=2)
    strategy: str = Field(default="")
    investment_style: str = Field(default="ACTIVE", min_length=1, max_length=50)
    shariah_status: str = Field(default="NOT_APPLICABLE", min_length=1, max_length=30)
    distribution_policy: str = Field(default="ACCUMULATING", min_length=1, max_length=80)
    review_frequency: str = Field(default="QUARTERLY", min_length=1, max_length=50)
    target_horizon_years: Optional[int] = Field(default=None, ge=1, le=50)
    inception_date: Optional[str] = None
    risk_level: int = Field(ge=1, le=5)
    minimum_investment: Decimal = Field(ge=0)
    management_fee: Decimal = Field(ge=0)
    performance_fee: Decimal = Field(ge=0)
    cost_basis_method: str = Field(default="AVERAGE_COST", min_length=1, max_length=30)
    benchmark: Optional[str] = Field(default=None, max_length=100)
    base_currency: str = Field(default="AED", min_length=3, max_length=3)
    liquidity_terms: str = Field(default="Daily", min_length=1, max_length=100)
    status: str = Field(default="DRAFT", pattern=r"^(ACTIVE|DRAFT|ARCHIVED)$")
    composition: ManagerCompositionIn = Field(default_factory=ManagerCompositionIn)

class ManagerPortfolioUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    vehicle_type: Optional[str] = Field(default=None, min_length=1, max_length=40)
    category: Optional[str] = Field(default=None, min_length=2, max_length=60)
    objective: Optional[str] = Field(default=None)
    strategy: Optional[str] = None
    investment_style: Optional[str] = Field(default=None, min_length=1, max_length=50)
    shariah_status: Optional[str] = Field(default=None, min_length=1, max_length=30)
    distribution_policy: Optional[str] = Field(default=None, min_length=1, max_length=80)
    review_frequency: Optional[str] = Field(default=None, min_length=1, max_length=50)
    target_horizon_years: Optional[int] = Field(default=None, ge=1, le=50)
    inception_date: Optional[str] = None
    risk_level: Optional[int] = Field(default=None, ge=1, le=5)
    minimum_investment: Optional[Decimal] = Field(default=None, ge=0)
    management_fee: Optional[Decimal] = Field(default=None, ge=0)
    performance_fee: Optional[Decimal] = Field(default=None, ge=0)
    cost_basis_method: Optional[str] = Field(default=None, min_length=1, max_length=30)
    benchmark: Optional[str] = Field(default=None, max_length=100)
    base_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    liquidity_terms: Optional[str] = Field(default=None, min_length=1, max_length=100)
    status: Optional[str] = Field(default=None, pattern=r"^(ACTIVE|DRAFT|ARCHIVED)$")

class ManagerInstrumentCreateIn(BaseModel):
    symbol: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    instrument_type: str = Field(min_length=1, max_length=50)
    asset_class: str = Field(min_length=1, max_length=80)
    currency: str = Field(default="AED", min_length=3, max_length=3)
    isin: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")

class ManagerDocumentCreateIn(BaseModel):
    document_type: str = Field(min_length=2, max_length=50)
    file_url: str = Field(min_length=5)
    version: str = Field(min_length=1, max_length=30)
    published: bool = True

class ManagerPerformanceIn(BaseModel):
    nav: Decimal = Field(ge=0)
    daily_return: Decimal = Field(default=0)
    monthly_return: Decimal = Field(default=0)
    ytd_return: Decimal = Field(default=0)

class ManagerVersionIn(BaseModel):
    notes: str = Field(default="", max_length=2000)
