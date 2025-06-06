from fastapi import HTTPException
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate, UserResponse
from database.connection import get_db
from utils.hash import hash_password

async def register_user(user: UserCreate):
    db = get_db()
    users_collection = db["users"]

    # Verificar si username o email ya existen
    existing_username = await users_collection.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username ya registrado")

    existing_email = await users_collection.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # Preparar usuario para insertar
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)  # 🔒 Hashear el password
    user_dict["isAdmin"] = False
    user_dict["isActive"] = False

    # Insertar usuario en base de datos
    result = await users_collection.insert_one(user_dict)

    # Crear respuesta sin el password
    response_user = UserResponse(
        id=str(result.inserted_id),
        name=user.name,
        lastname=user.lastname,
        username=user.username,
        email=user.email,
        isAdmin=False,
        isActive=False
    )

    return response_user

async def register_client(client: ClientCreate):
    db = get_db()
    client_collection = db["clients"]

    # Verificar si la cédula ya existe
    existing_cedula = await client_collection.find_one({"cedula": client.cedula})
    if existing_cedula:
        raise HTTPException(status_code=400, detail="Cédula ya registrada")

    # Verificar si el email ya existe
    existing_email = await client_collection.find_one({"email": client.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # Preparar cliente para insertar
    client_dict = client.dict()

    # Insertar cliente en base de datos
    result = await client_collection.insert_one(client_dict)

    # Retornar cliente con _id convertido a string
    return ClientResponse(id=str(result.inserted_id), **client_dict)