from fastapi import APIRouter
from controllers import loan_controller
from schemas.loan_schema import LoanCreate

loans_router = APIRouter()

@loans_router.post("/create")
async def create_loan_route(loan_data: LoanCreate):
    new_loan = await loan_controller.create_loan(loan_data)
    return new_loan
