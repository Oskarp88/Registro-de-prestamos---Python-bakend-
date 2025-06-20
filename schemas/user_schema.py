from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str
    lastname: str
    username: str
    email: EmailStr
    password: str
    isAdmin: bool = False
    isActive: bool = False
    creation_date: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    name: str
    lastname: str
    username: str
    email: EmailStr
    isAdmin: bool
    isActive: bool
    creation_date: datetime

