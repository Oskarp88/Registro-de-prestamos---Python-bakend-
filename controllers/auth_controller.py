from fastapi import HTTPException
from database.connection import get_db
from models.user_login_model import UserLogin
from schemas.user_schema import UserResponse
from utils.constants import Constants
from utils.hash import verify_password

async def login_user(user_data: UserLogin):
    db = get_db()
    users_collection = db[Constants.USERS]  # "users"

    # Buscar usuario por username o email
    user = await users_collection.find_one({
        "$or": [
            {Constants.USERNAME: user_data.username_or_email},
            {Constants.EMAIL: user_data.username_or_email}
        ]
    })

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas: el usuario o correo no existe.")

    # Verificar contraseña
    if not verify_password(user_data.password, user[Constants.PASSWORD]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas: contraseña incorrecta.")

    # Verificar si la cuenta está activa
    if not user[Constants.IS_ACTIVE]:
        raise HTTPException(
            status_code=403,
            detail="Credenciales correctas, pero tu cuenta aún no está activa. Por favor, espera a que un administrador la habilite."
        )

    # Login exitoso
    print({"message": "Inicio de sesión exitoso", "user": str(user["_id"])})
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
