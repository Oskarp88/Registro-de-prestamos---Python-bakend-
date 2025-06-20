from fastapi import HTTPException
from models.user_login_model import UserLogin
from schemas.user_schema import UserResponse
from utils.constants import Constants
from utils.hash import verify_password
from database.connection import database  

async def login_user(user_data: UserLogin):
    users_collection = database[Constants.USERS]  # "users"

    user = await users_collection.find_one({
        "$or": [
            {Constants.USERNAME: user_data.username_or_email},
            {Constants.EMAIL: user_data.username_or_email}
        ]
    })

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas: el usuario o correo no existe.")

    if not verify_password(user_data.password, user[Constants.PASSWORD]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas: contraseña incorrecta.")

    if not user[Constants.IS_ACTIVE]:
        raise HTTPException(
            status_code=403,
            detail="Credenciales correctas, pero tu cuenta aún no está activa. Por favor, espera a que un administrador la habilite."
        )

    return {
        "message": "Inicio de sesión exitoso.",
        "user": UserResponse(
            id=str(user["_id"]),
            name=user[Constants.NAME],
            lastname=user[Constants.LASTNAME],
            username=user[Constants.USERNAME],
            email=user[Constants.EMAIL],
            creation_date=user[Constants.CREATION_DATE],
            isAdmin=user[Constants.IS_ADMIN],
            isActive=user[Constants.IS_ACTIVE]
        )
    }
