import os
from sqlalchemy.engine import make_url

PRODUCT_NAME=os.getenv("PRODUCT_NAME","X Company")
PRODUCT_SLUG=os.getenv("PRODUCT_SLUG","x-company")

_default_db="sqlite:////tmp/xcompany.db"
_raw_db=os.getenv("DATABASE_URL","").strip()

# Supabase commonly provides a PostgreSQL URI; this project uses psycopg v3.
# Normalize postgres:// and postgresql:// to the installed psycopg dialect.
if _raw_db:
    if _raw_db.startswith("postgres://"):
        _raw_db="postgresql+psycopg://"+_raw_db[len("postgres://"):]
    elif _raw_db.startswith("postgresql://"):
        _raw_db="postgresql+psycopg://"+_raw_db[len("postgresql://"):]
    try:
        make_url(_raw_db)
        DATABASE_URL=_raw_db
    except Exception:
        # Keep local development resilient; never silently fall back on Vercel.
        if os.getenv("VERCEL") == "1":
            raise RuntimeError("DATABASE_URL is set but is not a valid SQLAlchemy database URL")
        DATABASE_URL=_default_db
else:
    if os.getenv("VERCEL") == "1":
        raise RuntimeError("DATABASE_URL is required in Vercel Production")
    DATABASE_URL=_default_db

JWT_SECRET=os.getenv("XCOMPANY_JWT_SECRET")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM","HS256")
CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:8000,http://127.0.0.1:8000").split(",") if x.strip()]

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")

SUPABASE_URL=os.getenv("SUPABASE_URL","").strip()
SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY","").strip()
SUPABASE_STORAGE_BUCKET=os.getenv("SUPABASE_STORAGE_BUCKET","portfolio-documents").strip() or "portfolio-documents"
