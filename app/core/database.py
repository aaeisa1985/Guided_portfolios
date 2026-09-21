from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import DATABASE_URL
from app.models import Base
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {},pool_pre_ping=True)
def get_db():
    with Session(engine) as db: yield db
