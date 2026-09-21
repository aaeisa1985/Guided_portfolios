"""Vercel entrypoint with temporary startup diagnostics."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app=FastAPI()

@app.get("/")
def startup_diagnostic():
    try:
        from app.main import app as real_app
        return JSONResponse(status_code=500,content={"error":"REAL_APP_NOT_MOUNTED","message":"Import succeeded inside request but Vercel entrypoint is using the diagnostic wrapper."})
    except Exception as exc:
        return JSONResponse(status_code=500,content={"error":"APP_IMPORT_FAILED","type":type(exc).__name__,"message":str(exc)})
