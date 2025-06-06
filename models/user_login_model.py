from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    username_or_email: str
    password: str
