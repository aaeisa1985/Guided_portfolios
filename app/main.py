"""Application entrypoint: configuration, middleware, routers and static frontend only."""
import secrets
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import CORS_ORIGINS,PRODUCT_NAME
from app.core.database import engine
from app.models import Base
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.portfolios import router as portfolios_router
from app.api.suitability import router as suitability_router
from app.api.simulator import router as simulator_router
from app.api.subscriptions import router as subscriptions_router
from app.api.consents import router as consents_router
from app.api.activity import router as activity_router
from app.api.dashboard import router as dashboard_router
from app.api.positions import router as positions_router
from app.api.admin import router as admin_router
from app.api.corporate_actions import router as corporate_actions_router
app=FastAPI(title=f"{PRODUCT_NAME} Guided Portfolios API",version="1.0.0",description="Institutional-grade Guided Portfolios platform foundation")
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Request-ID","X-Idempotency-Key"])
@app.middleware("http")
async def security_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"; response.headers["X-Frame-Options"]="DENY"; response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"; response.headers["X-Request-ID"]=request.headers.get("X-Request-ID",secrets.token_hex(8))
    return response
for router in [health_router,auth_router,portfolios_router,suitability_router,simulator_router,subscriptions_router,consents_router,activity_router,dashboard_router,positions_router,admin_router,corporate_actions_router]: app.include_router(router)
app.mount("/frontend",StaticFiles(directory="frontend"),name="frontend")
@app.get("/",include_in_schema=False)
def frontend_home(): return FileResponse("frontend/index.html")
