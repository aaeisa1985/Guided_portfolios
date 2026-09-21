"""Vercel entrypoint with temporary import diagnostics."""
try:
    from app.main import app
except Exception as exc:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app=FastAPI()
    @app.get("/")
    def startup_diagnostic():
        return JSONResponse(status_code=500,content={"error":"APP_IMPORT_FAILED","type":type(exc).__name__,"message":str(exc)})
