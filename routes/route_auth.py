from fastapi import APIRouter
from models.user_login_model import UserLogin
from controllers.auth_controller import login_user

route_auth = APIRouter()

@route_auth.post("/login")
async def login_route(user_data: UserLogin):
    return await login_user(user_data)
