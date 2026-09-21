import os
from sqlalchemy.engine import make_url

PRODUCT_NAME=os.getenv("PRODUCT_NAME","X Company")
PRODUCT_SLUG=os.getenv("PRODUCT_SLUG","x-company")

_default_db="sqlite:////tmp/xcompany.db"
_raw_db=os.getenv("DATABASE_URL","").strip()
try:
    make_url(_raw_db)
    DATABASE_URL=_raw_db
except Exception:
    DATABASE_URL=_default_db

JWT_SECRET=os.getenv("XCOMPANY_JWT_SECRET")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM","HS256")
CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:8000,http://127.0.0.1:8000").split(",") if x.strip()]
