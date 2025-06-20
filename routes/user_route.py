from typing import List

from bson import ObjectId
from controllers.user_controller import get_accounts, get_all_clients, get_client_by_id, get_history_capital, get_history_ganancias, register_client, register_user, search_clients_controller, update_accounts
from fastapi import APIRouter, HTTPException, Query
from database.connection import database
from schemas.capital_schema import CapitalUpdateRequest
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate
from utils.constants import Constants
from utils.erialize_notifications import serialize_notifications

user_router = APIRouter()

@user_router.post("/register")
async def register(user: UserCreate):
    new_user = await register_user(user)
    return {"message": "Usuario registrado correctamente", "user": new_user}

@user_router.post("/client/register")
async def registerClient(client: ClientCreate):
    new_client = await register_client(client)
    return {"message": "Client registrado correctamente", "user": new_client}

@user_router.get("/client/all", response_model=List[ClientResponse])
async def getClients():
    return await get_all_clients()

@user_router.get("/client")
async def get_client(client_id: str = Query(..., description="ID del cliente")):
    return await get_client_by_id(client_id)

@user_router.get("/clients/search", response_model=List[ClientResponse])
async def search_clients(query: str = Query(..., min_length=1)):
    return await search_clients_controller(query)

@user_router.get("/capital")
async def getAccounts():
    return await get_accounts()

@user_router.get("/history-capital")
async def getHistoryCapital():
    return await get_history_capital()

@user_router.get("/history-ganancias")
async def getHistoryGanancias():
    return await get_history_ganancias()

@user_router.put("/capital/update")
async def update_accounts_route(data: CapitalUpdateRequest):
    new_capital = await update_accounts(data.capital)
    return new_capital

@user_router.post("/notifications/mark_read/{user_id}")
async def mark_notifications_read(user_id: str):
    db = database
    notifications_collection = db[Constants.NOTIFICATIONS]

    result = await notifications_collection.update_many(
        {
            "read_by": {"$ne": user_id}  # si NO lo ha leído este usuario
        },
        {
            "$addToSet": {"read_by": user_id}  # agrégalo sin duplicar
        }
    )

    return {"modified_count": result.modified_count}

@user_router.get("/notifications/{user_id}")
async def get_notifications(user_id: str):
    db = database
    users_collection = db[Constants.USERS]
    notifications_collection = db[Constants.NOTIFICATIONS]

    # Obtener usuario y su fecha de creación
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_creation_date = user.get("creation_date")
    if not user_creation_date:
        raise HTTPException(status_code=400, detail="Usuario sin fecha de creación")

    # Solo notificaciones posteriores a la creación del usuario
    cursor = notifications_collection.find({
        "creation_date": {"$gte": user_creation_date}
    }).sort("creation_date", -1).limit(100)

    notifications = await cursor.to_list(length=100)

    # Serializar notificaciones
    serializable = []
    for notif in notifications:
        notif['_id'] = str(notif['_id'])
        if 'client_id' in notif and isinstance(notif['client_id'], ObjectId):
            notif['client_id'] = str(notif['client_id'])
        serializable.append(notif)

    # Calcular cuántas no han sido leídas por ese usuario
    unread_count = sum(
        1 for notif in serializable if user_id not in notif.get("read_by", [])
    )

    return {
        "notifications": serialize_notifications(serializable),
        "unread_count": unread_count
    }


