from pydantic import BaseModel,EmailStr,Field
class RegisterIn(BaseModel):
    full_name:str; email:EmailStr; password:str=Field(min_length=8); mobile:str|None=None
class LoginIn(BaseModel):
    email:EmailStr; password:str
class TokenOut(BaseModel):
    access_token:str; token_type:str="bearer"
