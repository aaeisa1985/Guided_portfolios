"""Authentication API compatibility module. Main endpoints remain in app.main for the MVP."""
from app.main import register, login, me
__all__=["register","login","me"]