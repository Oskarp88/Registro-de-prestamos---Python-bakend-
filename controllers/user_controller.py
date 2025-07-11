from datetime import datetime
import re
from typing import List
from bson import ObjectId
from fastapi import HTTPException
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate, UserResponse
from database.connection import database
from utils.constants import Constants
from utils.hash import hash_password

async def register_user(user: UserCreate):
    db = database
    users_collection = db[Constants.USERS]

    existing_username = await users_collection.find_one({Constants.USERNAME: user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username ya registrado")

    existing_email = await users_collection.find_one({Constants.EMAIL: user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user_dict = user.dict()
    user_dict[Constants.PASSWORD] = hash_password(user.password)  
    user_dict[Constants.IS_ADMIN] = False
    user_dict[Constants.IS_ACTIVE] = False
    user_dict[Constants.CREATION_DATE] = datetime.utcnow()

    result = await users_collection.insert_one(user_dict)
    new_user = await users_collection.find_one({"_id": result.inserted_id})

    response_user = UserResponse(
        id=str(new_user["_id"]),
        name=new_user[Constants.NAME],
        lastname=new_user[Constants.LASTNAME],
        username=new_user[Constants.USERNAME],
        email=new_user[Constants.EMAIL],  
        isAdmin=new_user[Constants.IS_ADMIN],
        isActive=new_user[Constants.IS_ACTIVE],
        creation_date=new_user[Constants.CREATION_DATE],
    )

    return response_user

async def register_client(client: ClientCreate):
    db = database
    client_collection = db[Constants.CLIENTS]

    # Verificar si la cédula ya existe
    existing_cedula = await client_collection.find_one({Constants.CEDULA: client.cedula})
    if existing_cedula:
        raise HTTPException(status_code=400, detail="Cédula ya registrada")

    client_dict = client.dict()

    result = await client_collection.insert_one(client_dict)

    return ClientResponse(id=str(result.inserted_id), **client_dict)

async def get_all_clients():
    db = database
    client_collection = db[Constants.CLIENTS]

    clients_cursor = client_collection.find()
    clients = []
    async for client in clients_cursor:
        client["id"] = str(client["_id"])
        client.pop("_id")
        clients.append(ClientResponse(**client))

    return clients

async def get_client_by_id(client_id: str):
    db = database
    client_collection = db[Constants.CLIENTS]

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
    db = database
    client_collection = db[Constants.CLIENTS]

    keywords = query.strip().split()

    if not keywords:
        raise HTTPException(status_code=400, detail="La consulta de búsqueda no puede estar vacía.")

    conditions = []
    for word in keywords:
        regex = re.compile(re.escape(word), re.IGNORECASE)
        conditions.append({Constants.NAME: {"$regex": regex}})
        conditions.append({Constants.LASTNAME: {"$regex": regex}})
        conditions.append({Constants.PHONE_NUMBER: {"$regex": regex}})
        if word.isdigit():
            conditions.append({Constants.CEDULA: int(word)})

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
    db = database
    accounts_collection = db[Constants.ACCOUNTS]
    
    accounts = await accounts_collection.find_one({})

    if accounts is None:
        raise HTTPException(status_code=404, detail=f"No se encontraron cuentas con ese ID.")

    return {
        Constants.CAPITAL: accounts[Constants.CAPITAL],
        Constants.ADMIN: accounts[Constants.ADMIN],
        Constants.GANANCIAS: accounts[Constants.GANANCIAS],
        Constants.TOTAL_INTEREST: accounts[Constants.HISTORY_INTEREST],
        Constants.HISTORY_CAPITAL_TOTAL: accounts[Constants.HISTORY_CAPITAL_TOTAL]
    }

async def update_accounts(capital: float):
    db = database
    accounts_collection = db[Constants.ACCOUNTS]

    await accounts_collection.update_one(
        {},  # Sin filtro → actualiza el unico documento, solo si hay un solo documento
        {
            "$inc": {
                Constants.CAPITAL: capital
            }
        }
    )

    new_capital = await accounts_collection.find_one({})

    if not new_capital:
       raise HTTPException(status_code=500, detail="No account document found.")
    
    return {
       Constants.MESSAGE: "Capital agregado con exito",
       Constants.NEW_CAPITAL: new_capital[Constants.CAPITAL],
       Constants.ADMIN: new_capital[Constants.ADMIN]
    }

async def get_history_capital():
    db = database
    history_collection = db[Constants.HISTORY_CAPITAL]

    history_cursor = history_collection.find({})
    history_list = []

    async for doc in history_cursor:
        doc["_id"] = str(doc["_id"])
        history_list.append(doc)

    if not history_list:
        raise HTTPException(status_code=404, detail="No se encontraron movimientos de capital.")

    return {
        Constants.TOTAL_MOVIMIENTOS: len(history_list),
        Constants.HISTORIAL: history_list
    }

async def get_history_ganancias():
    db = database
    history_collection = db[Constants.HISTORY_GANANCIAS]

    history_cursor = history_collection.find({})
    history_list = []

    async for doc in history_cursor:
        doc["_id"] = str(doc["_id"])
        history_list.append(doc)

    if not history_list:
        raise HTTPException(status_code=404, detail="No se encontraron movimientos de ganancias.")

    return {
        Constants.TOTAL_MOVIMIENTOS: len(history_list),
        Constants.HISTORY_GANANCIAS: history_list
    }