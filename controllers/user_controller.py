import re
from typing import List
from bson import ObjectId
from fastapi import HTTPException
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate, UserResponse
from database.connection import get_db
from utils.hash import hash_password
from dotenv import load_dotenv
import os

load_dotenv()

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

async def get_client_by_id(client_id: str):
    db = get_db()
    client_collection = db["clients"]

    # Verificar el id
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID de cliente inválido.")

    client = await client_collection.find_one({"_id": ObjectId(client_id)})

    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # convertir el id a str
    client["id"] = str(client["_id"])
    client.pop("_id")

    return ClientResponse(**client)

async def search_clients_controller(query: str) -> List[ClientResponse]:
    db = get_db()
    client_collection = db["clients"]

    keywords = query.strip().split()

    if not keywords:
        raise HTTPException(status_code=400, detail="La consulta de búsqueda no puede estar vacía.")

    conditions = []
    for word in keywords:
        regex = re.compile(re.escape(word), re.IGNORECASE)
        conditions.append({"name": {"$regex": regex}})
        conditions.append({"lastname": {"$regex": regex}})
        conditions.append({"phoneNumber": {"$regex": regex}})
        if word.isdigit():
            conditions.append({"cedula": int(word)})

    cursor = client_collection.find({"$or": conditions})
    clients = await cursor.to_list(length=None)

    if not clients:
        raise HTTPException(status_code=404, detail="No se encontraron clientes con esa búsqueda.")

    result = []
    for client in clients:
        client["id"] = str(client["_id"])
        client.pop("_id")
        result.append(ClientResponse(**client))

    return result

async def get_accounts():
    db = get_db()
    accounts_collection = db["accounts"]
    accounts_id= os.getenv("ACCOUNTS_ID")
    accounts = await accounts_collection.find_one({'_id': ObjectId(accounts_id) })

    return {
        "capital": accounts["capital"],
        "admin" : accounts["admin"],
        "ganancias": accounts["ganancias"]
    }

async def update_accounts(capital: float):
    db = get_db()
    accounts_collection = db['accounts']

    await accounts_collection.update_one(
        {},  # Sin filtro → actualiza el unico documento, solo si hay un solo documento
        {
            "$inc": {
                "capital": capital
            }
        }
    )

    new_capital = await accounts_collection.find_one({})

    if not new_capital:
       raise HTTPException(status_code=500, detail="No account document found.")
    
    return {
       "message": "Capital agregado con exito",
       "new_capital": new_capital['capital'],
       "admin": new_capital['admin']
    }

async def get_history_capital():
    db = get_db()
    history_collection = db["historyCapital"]

    history_cursor = history_collection.find({})
    history_list = []

    async for doc in history_cursor:
        doc["_id"] = str(doc["_id"])
        history_list.append(doc)

    if not history_list:
        raise HTTPException(status_code=404, detail="No se encontraron movimientos de capital.")

    return {
        "total_movimientos": len(history_list),
        "historial": history_list
    }

async def get_history_ganancias():
    db = get_db()
    history_collection = db["historyGanancias"]

    history_cursor = history_collection.find({})
    history_list = []

    async for doc in history_cursor:
        doc["_id"] = str(doc["_id"])
        history_list.append(doc)

    if not history_list:
        raise HTTPException(status_code=404, detail="No se encontraron movimientos de ganancias.")

    return {
        "total_movimientos": len(history_list),
        "historial": history_list
    }