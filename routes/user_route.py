from typing import List
from controllers.user_controller import get_accounts, get_all_clients, get_client_by_id, get_history_capital, get_history_ganancias, register_client, register_user, search_clients_controller, update_accounts
from fastapi import APIRouter, Query
from schemas.capital_schema import CapitalUpdateRequest
from schemas.client_schema import ClientCreate, ClientResponse
from schemas.user_schema import UserCreate

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
