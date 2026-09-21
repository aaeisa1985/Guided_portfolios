"""Central configuration surface for the MVP."""
import os
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./emcoin.db")
JWT_SECRET=os.getenv("JWT_SECRET","change-me-in-production")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM","HS256")