from datetime import datetime, timedelta
import random
from bson import ObjectId
from fastapi import HTTPException
from models.user_login_model import UserLogin
from schemas.forgot_password_request import ForgotPasswordRequest
from schemas.reset_password_request import ResetPasswordRequest
from schemas.user_schema import UserResponse
from schemas.verify_code_request import VerifyCodeRequest
from utils.constants import Constants
from utils.generate_token import create_access_token
from utils.hash import hash_password, verify_password
from database.connection import database
from utils.mail import send_reset_code_email  

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

    if user[Constants.IS_ADMIN]:
    # Expira en 15 minutos
        token_expiry = timedelta(minutes=15)
    else:
        # Expira en 7 días
        token_expiry = timedelta(days=7)

    token = create_access_token({"sub": str(user["_id"]), "role": "admin" if user[Constants.IS_ADMIN] else "user"}, token_expiry)

    return {
        "access_token": token,
        "message": "Inicio de sesión exitoso.",
        "token_type": "bearer",
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

async def forgot_password(data: ForgotPasswordRequest):
    users = database[Constants.USERS]
    codes = database["password_reset_codes"]

    user = await users.find_one({
        "$or": [
            {Constants.EMAIL: data.email_or_username},
            {Constants.USERNAME: data.email_or_username}
        ]
    })

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Generar código de 6 dígitos
    code = str(random.randint(100000, 999999))

    # Guardar en DB
    await codes.insert_one({
        "user_id": user["_id"],
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    })

    # Enviar correo
    await send_reset_code_email(user[Constants.EMAIL], user[Constants.NAME], code)

    return {"message": "Código de recuperación enviado al correo"}


async def verify_code(data: VerifyCodeRequest):
    users = database[Constants.USERS]
    codes = database["password_reset_codes"]

    user = await users.find_one({
        "$or": [
            {Constants.EMAIL: data.email_or_username},
            {Constants.USERNAME: data.email_or_username}
        ]
    })

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    code_entry = await codes.find_one({
        "user_id": user["_id"],
        "code": data.code
    })

    if not code_entry:
        raise HTTPException(status_code=400, detail="Código incorrecto")

    if code_entry["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="El código ha expirado")

    return {"message": "Código válido", "user_id": str(user["_id"])}



async def reset_password(data: ResetPasswordRequest):
    users = database[Constants.USERS]
    codes = database["password_reset_codes"]

    # Verifica si hay un código activo
    active_code = await codes.find_one({
        "user_id": ObjectId(data.user_id),
        "expires_at": {"$gt": datetime.utcnow()}
    })

    if not active_code:
        raise HTTPException(status_code=403, detail="Código expirado. Solicita uno nuevo.")

    hashed = hash_password(data.new_password)
    result = await users.update_one(
        {"_id": ObjectId(data.user_id)},
        {"$set": {Constants.PASSWORD: hashed}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No se pudo actualizar la contraseña")

    # Eliminar codigo
    await codes.delete_many({"user_id": ObjectId(data.user_id)})

    return {"message": "Contraseña restablecida correctamente"}