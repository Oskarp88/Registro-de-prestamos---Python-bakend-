from fastapi import APIRouter
from models.user_login_model import UserLogin
from controllers.auth_controller import forgot_password, login_user, reset_password, verify_code
from schemas.forgot_password_request import ForgotPasswordRequest
from schemas.reset_password_request import ResetPasswordRequest
from schemas.verify_code_request import VerifyCodeRequest

route_auth = APIRouter()

@route_auth.post("/login")
async def login_route(user_data: UserLogin):
    return await login_user(user_data)

@route_auth.post("/forgot-password")
async def forgot_password_route(data: ForgotPasswordRequest):
    return await forgot_password(data)

@route_auth.post("/verify-reset-code")
async def verify_code_route(data: VerifyCodeRequest):
    return await verify_code(data)
    
@route_auth.post("/reset-password")
async def  reset_password_route(data: ResetPasswordRequest):
    return await reset_password(data)