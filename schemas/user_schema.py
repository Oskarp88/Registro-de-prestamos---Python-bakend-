from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    lastname: str
    username: str
    email: EmailStr
    password: str
    isAdmin: bool = False
    isActive: bool = False

class UserResponse(BaseModel):
    id: str
    name: str
    lastname: str
    username: str
    email: EmailStr
    isAdmin: bool
    isActive: bool

