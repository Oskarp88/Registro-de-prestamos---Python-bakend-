from fastapi import APIRouter
from controllers import account_controller
from schemas.account_schemas import CapitalOperationRequest, TransferRequest

accounts_router = APIRouter()

@accounts_router.post("/add-capital")
async def add_capital(data: CapitalOperationRequest):
    return await account_controller.add_capital(data.amount)

@accounts_router.post("/withdraw-ganancias")
async def withdraw_ganancias(data: CapitalOperationRequest):
    return await account_controller.withdraw_ganancias(data.amount)

@accounts_router.post("/transfer-capital-to-ganancias")
async def transfer_capital_to_ganancias(data: TransferRequest):
    return await account_controller.transfer_capital_to_ganancias(data.amount)

@accounts_router.post("/transfer-ganancias-to-capital")
async def transfer_ganancias_to_capital(data: TransferRequest):
    return await account_controller.transfer_ganancias_to_capital(data.amount)
