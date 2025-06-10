from fastapi import HTTPException
from database.connection import get_db
from models.user_login_model import UserLogin
from schemas.user_schema import UserResponse
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
    
    print('username o email: ',user_data.username_or_email)
    if not user:
        print('no existe: ', user_data.username_or_email)
        raise HTTPException(status_code=401, detail="Credenciales inválidas: email no existe")

    # Verificar password
    if not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas: contraseña incorrecta")

    # Login exitoso
    print({"message": "Inicio de sesión exitoso", "user": str(user["_id"])})
    return {"message": "Inicio de sesión exitoso", "user": UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        lastname=user["lastname"],
        username=user["username"],
        email=user["email"],
        isAdmin=False,
        isActive=False
    )}
