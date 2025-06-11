from controllers.loan_controller import create_loan, get_loan_by_client_id
from fastapi import APIRouter
from schemas.loan_schema import LoanCreate

loans_router = APIRouter()

@loans_router.post("/create")
async def create_loan_route(loan_data: LoanCreate):
    new_loan = await create_loan(loan_data)
    return new_loan

@loans_router.get("/get-by-client/{client_id}")
async def get_loan_by_client_id_route(client_id: str):
    loan = await get_loan_by_client_id(client_id)
    return loan