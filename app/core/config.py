import os
PRODUCT_NAME=os.getenv("PRODUCT_NAME","X Company")
PRODUCT_SLUG=os.getenv("PRODUCT_SLUG","x-company")
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./data/xcompany.db")
JWT_SECRET=os.getenv("XCOMPANY_JWT_SECRET")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM","HS256")
CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:8000,http://127.0.0.1:8000").split(",") if x.strip()]
if not JWT_SECRET or JWT_SECRET=="dev-only-change-this-secret":
    raise RuntimeError("XCOMPANY_JWT_SECRET must be set to a strong secret before starting the API")
if DATABASE_URL.startswith("sqlite:///./data/"): os.makedirs("data",exist_ok=True)
