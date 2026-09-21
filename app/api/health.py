from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine
from app.core.config import PRODUCT_SLUG
router=APIRouter(tags=["health"])
@router.get("/health")
def health(): return {"status":"ok","service":f"{PRODUCT_SLUG}-guided-portfolios","version":"1.0.0"}
@router.get("/health/ready")
def readiness():
    with Session(engine) as s: s.execute(select(1))
    return {"status":"ready","database":"ok"}
