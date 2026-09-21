from datetime import datetime,timedelta,timezone
from typing import Optional
from uuid import UUID
from fastapi import Header,HTTPException
from jose import jwt,JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import JWT_ALGORITHM,JWT_SECRET
from app.core.database import engine
from app.models import Customer
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
def hash_password(password): return pwd.hash(password)
def verify_password(password,password_hash): return pwd.verify(password,password_hash)
def token_for(c):
    exp=int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())
    return jwt.encode({"sub":str(c.id),"role":c.role,"exp":exp},JWT_SECRET,algorithm=JWT_ALGORITHM)
def current_user(authorization:Optional[str]=Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "): raise HTTPException(401,"Authentication required")
    try:
        payload=jwt.decode(authorization.split()[1],JWT_SECRET,algorithms=[JWT_ALGORITHM]); cid=UUID(payload["sub"])
    except (JWTError,ValueError,KeyError): raise HTTPException(401,"Invalid token")
    with Session(engine) as s:
        c=s.get(Customer,cid)
        if not c: raise HTTPException(401,"Customer not found")
        return c


def admin_token_for(username):
    if not JWT_SECRET:
        raise RuntimeError("XCOMPANY_JWT_SECRET is required for admin authentication")
    exp=int((datetime.now(timezone.utc)+timedelta(hours=2)).timestamp())
    return jwt.encode(
        {"sub":username,"role":"ADMIN","admin":True,"exp":exp},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

def current_admin(authorization:Optional[str]=Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Admin authentication required")
    try:
        payload=jwt.decode(authorization.split()[1],JWT_SECRET,algorithms=[JWT_ALGORITHM])
        if payload.get("role")!="ADMIN" or payload.get("admin") is not True or not payload.get("sub"):
            raise HTTPException(403,"Admin access required")
        return {"username":payload["sub"],"role":"ADMIN"}
    except HTTPException:
        raise
    except (JWTError,ValueError,KeyError):
        raise HTTPException(401,"Invalid admin token")
