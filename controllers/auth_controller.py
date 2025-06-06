from fastapi import HTTPException
from database.connection import get_db
from models.user_login_model import UserLogin
from utils.hash import verify_password

async def login_user(user_data: UserLogin):
    db = get_db()
    users_collection = db["users"]

    # Buscar usuario por username o email
    user = await users_collection.find_one({
        "$or": [
            {"username": user_data.username_or_email},
            {"email": user_data.username_or_email}
        ]
    })

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar password
    if not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Login exitoso, puedes crear y devolver JWT aquí si quieres
    return {"message": "Inicio de sesión exitoso", "user": str(user["_id"])}
