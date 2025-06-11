from fastapi import HTTPException
from database.connection import get_db
from schemas.loan_schema import LoanCreate, PaymentHistoryItem
from bson import ObjectId
from datetime import datetime, timedelta

async def create_loan(loan_data: LoanCreate):
    db = get_db()
    loans_collection = db["loans"]
    clients_collection = db["clients"]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")


    # Calcular interés del 15%
    interest = round(loan_data.total_loan * 0.15, 2)

    # Crear documento de deuda
    loan_dict = loan_data.dict()
    loan_dict["client_id"] = ObjectId(loan_data.client_id)
    loan_dict["total_loan"] = loan_data.total_loan
    loan_dict["interest"] = interest
    loan_dict["payment_amount"] = loan_data.payment_amount
    # loan_dict["creation_date"] = datetime.utcnow()
    loan_dict["status"] = "pendiente"
    loan_dict["history"] = []

    result = await loans_collection.insert_one(loan_dict)

    loan_dict["_id"] = str(result.inserted_id)
    loan_dict["client_id"] = str(loan_dict["client_id"])

    return loan_dict

async def get_loan_by_client_id(client_id: str):
    db = get_db()
    loans_collection = db["loans"]

    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="No se encontró préstamo para este cliente")

    loan["_id"] = str(loan["_id"])
    loan["client_id"] = str(loan["client_id"])

    return loan
