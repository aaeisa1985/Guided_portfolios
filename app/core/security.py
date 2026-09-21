"""Security helpers exposed independently for future modularization."""
from app.main import pwd, token_for, current_user
hash_password=pwd.hash
verify_password=pwd.verify