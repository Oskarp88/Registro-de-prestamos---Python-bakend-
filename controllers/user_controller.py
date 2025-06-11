from fastapi import HTTPException
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate, UserResponse
from database.connection import get_db
from utils.hash import hash_password

async def register_user(user: UserCreate):
    db = get_db()
    users_collection = db["users"]

    existing_username = await users_collection.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username ya registrado")

    existing_email = await users_collection.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)  
    user_dict["isAdmin"] = False
    user_dict["isActive"] = False

    result = await users_collection.insert_one(user_dict)

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

    client_dict = client.dict()

    result = await client_collection.insert_one(client_dict)

    return ClientResponse(id=str(result.inserted_id), **client_dict)

async def get_all_clients():
    db = get_db()
    client_collection = db["clients"]

    clients_cursor = client_collection.find()
    clients = []
    async for client in clients_cursor:
        client["id"] = str(client["_id"])
        client.pop("_id")
        clients.append(ClientResponse(**client))

    return clients