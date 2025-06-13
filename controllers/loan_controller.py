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

from fastapi import HTTPException
from database.connection import get_db
from bson import ObjectId
from datetime import datetime
from calendar import monthrange

async def update_interest_payment(client_id: str, paid_interest: float):
    db = get_db()
    loans_collection = db["loans"]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    current_interest = loan.get("interest", 0)
    current_due_date_str = loan.get("due_date")

    if not current_due_date_str:
        raise HTTPException(status_code=400, detail="Loan has no due date set")

    # Convertir dueDate string a datetime
    current_due_date = datetime.strptime(current_due_date_str, "%Y-%m-%d")

    # Calcular nuevo mes y año
    new_month = current_due_date.month + 1
    new_year = current_due_date.year

    if new_month > 12:
        new_month = 1
        new_year += 1

    # Validar el día del nuevo mes
    last_day_of_new_month = monthrange(new_year, new_month)[1]
    new_day = min(current_due_date.day, last_day_of_new_month)

    # Crear nueva fecha segura
    new_due_date = current_due_date.replace(year=new_year, month=new_month, day=new_day)
    new_due_date_str = new_due_date.strftime("%Y-%m-%d")

    # Verificar pago parcial o completo
    if paid_interest < current_interest:
        status = "pago parcial"
        message = "Partial payment recorded successfully"
    else:
        status = "pago completado"
        message = "Full payment recorded successfully"

    # Actualizar loan
    await loans_collection.update_one(
        {"client_id": ObjectId(client_id)},
        {
            "$set": {
                "status": status, 
                "due_date": new_due_date_str
            },
            "$push": {
                "history": {
                    "date": datetime.utcnow(),
                    "status": status,
                    "due_date": current_due_date_str,
                    "interestPayment": paid_interest,
                    "paymentAmount": 0
                }
            }
        }
    )


    return {"message": message, "new_due_date": new_due_date_str, "status": status}


async def update_payment(client_id: str, payment_amount: float):
    db = get_db()
    loans_collection = db["loans"]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    current_due_date_str = loan.get("due_date")

    if not current_due_date_str:
        raise HTTPException(status_code=400, detail="Loan has no due date set")

    # Calcula el nuevo total_loan
    new_total_loan = loan["total_loan"] - payment_amount

     # Calcular interés del 15%
    interest = round( new_total_loan * 0.15, 2)

    # Obtiene el historial actual
    loan_history = loan.get("history", [])

    if not loan_history:
        raise HTTPException(status_code=400, detail="No payment history found for this loan")

    # Actualiza el último elemento del historial
    last_index = len(loan_history) - 1
    loan_history[last_index]["paymentAmount"] = payment_amount
    loan_history[last_index]["date"] = datetime.utcnow()

    await loans_collection.update_one(
        {"client_id": ObjectId(client_id)},
        {
            "$set": {
                "total_loan": new_total_loan,
                "interest": interest,
                "history": loan_history,
                "dueDate": loan_history[last_index]["due_date"]
            }
        }
    )

    return {
        "message": "Payment and history updated successfully",
        "total_loan": new_total_loan,
        "interest": interest,
        "history": loan_history
    }

  