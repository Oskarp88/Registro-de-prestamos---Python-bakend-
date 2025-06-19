from pydantic import BaseModel, EmailStr, constr

class ClientCreate(BaseModel):
    name: str
    lastname: str
    cedula: int
    phoneNumber: constr(min_length=10, max_length=10, pattern=r'^\d+$') # type: ignore
    

class ClientResponse(BaseModel):
    id: str
    name: str
    lastname: str
    cedula: int
    phoneNumber: constr(min_length=10, max_length=10, pattern=r'^\d+$') # type: ignore