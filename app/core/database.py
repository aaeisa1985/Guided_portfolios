from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from app.core.config import DATABASE_URL
from app.models import Base

_is_sqlite=DATABASE_URL.startswith("sqlite")
_is_transaction_pooler=(":6543/" in DATABASE_URL) or (":6543?" in DATABASE_URL)

connect_args={"check_same_thread":False} if _is_sqlite else {}
if not _is_sqlite:
    # Supabase transaction pooler (serverless): disable psycopg prepared statements.
    if _is_transaction_pooler:
        connect_args["prepare_threshold"]=None
    # Always require TLS for PostgreSQL connections.
    connect_args["sslmode"]="require"

engine=create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    poolclass=NullPool if _is_transaction_pooler else None,
)

def get_db():
    with Session(engine) as db:
        yield db
