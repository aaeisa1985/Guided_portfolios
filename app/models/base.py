from enum import Enum
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
class Role(str, Enum):
    investor="INVESTOR"; manager="MANAGER"; admin="ADMIN"
