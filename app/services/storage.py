from pathlib import Path
from uuid import uuid4
from urllib.parse import quote
from app.core.config import SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY,SUPABASE_STORAGE_BUCKET

ALLOWED_MIME={"application/pdf"}

def _client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase Storage is not configured")
    from supabase import create_client
    return create_client(SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY)

def create_upload(filename:str,content_type:str,portfolio_id):
    if content_type not in ALLOWED_MIME:
        raise ValueError("Only PDF documents are supported")
    safe=Path(filename).name.replace(" ","_")
    path=f"portfolios/{portfolio_id}/{uuid4().hex}_{safe}"
    response=_client().storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_upload_url(path,options={"upsert":False})
    data=getattr(response,"data",response)
    if isinstance(data,dict): return {"bucket":SUPABASE_STORAGE_BUCKET,"path":path,"signedUrl":data.get("signedUrl"),"token":data.get("token")}
    raise RuntimeError("Storage upload URL generation failed")

def create_download(path:str,expires_in:int=900):
    prefix=f"storage://{SUPABASE_STORAGE_BUCKET}/"
    clean=path[len(prefix):] if path.startswith(prefix) else path
    response=_client().storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_url(clean,expires_in)
    data=getattr(response,"data",response)
    if isinstance(data,dict): return data.get("signedUrl")
    raise RuntimeError("Storage download URL generation failed")
