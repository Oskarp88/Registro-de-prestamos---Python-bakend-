from controllers.loan_controller import create_loan, get_all_loan_client, get_loan_by_client_id, get_pending_loans_with_total_interest, update_full_payment, update_interest_payment, update_loan, update_payment
from fastapi import APIRouter
from schemas.full_payment import FullPayment
from schemas.interest_payment_request import InterestPaymentRequest
from schemas.loan_schema import LoanCreate
from schemas.payment_amount import PaymentAmount

loans_router = APIRouter()

@loans_router.post("/create")
async def create_loan_route(loan_data: LoanCreate):
    new_loan = await create_loan(loan_data)
    return new_loan

@loans_router.put("/update")
async def create_loan_route(loan_data: LoanCreate):
    new_loan = await update_loan(loan_data)
    return new_loan

@loans_router.get("/get-by-client/{client_id}")
async def get_loan_by_client_id_route(client_id: str):
    loan = await get_loan_by_client_id(client_id)
    return loan

@loans_router.get("/get-all-loans")
async def get_loan_client():
    loan = await get_all_loan_client()
    return loan

@loans_router.put("/pay-interest")
async def pay_interest(payload: InterestPaymentRequest):
    print('client_id: ', payload.client_id, 'paid_interest: ', payload.paid_interest)
    return await update_interest_payment(payload.client_id, payload.paid_interest)

@loans_router.put("/pay_amount")
async def pay_interest(payload: PaymentAmount):
    print('client_id: ', payload.client_id, 'payment_amount: ', payload.payment_amount)
    return await update_payment(payload.client_id, payload.payment_amount)

@loans_router.put("/pay_full")
async def pay_interest(payload: FullPayment):
    print('client_id: ', payload.client_id)
    return await update_full_payment(payload.client_id)

@loans_router.get("/get/pending")
async def get():
    loan = await get_pending_loans_with_total_interest()
    return loan