"""Database compatibility surface; the MVP engine remains defined in app.main."""
from app.main import engine, Base
from sqlalchemy.orm import Session
def get_db():
    with Session(engine) as db: yield db