from controllers.user_controller import register_client, register_user
from fastapi import APIRouter
from schemas.client_schema import ClientCreate
from schemas.user_schema import UserCreate

user_router = APIRouter()

@user_router.post("/register")
async def register(user: UserCreate):
    new_user = await register_user(user)
    return {"message": "Usuario registrado correctamente", "user": new_user}

@user_router.post("/client/register")
async def registerClient(client: ClientCreate):
    new_client = await register_client(client)
    return {"message": "Client registrado correctamente", "user": new_client}
