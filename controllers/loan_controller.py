from fastapi import HTTPException
from database.connection import get_db
from schemas.historyCapital import HistoryCapitalCreate
from schemas.historyGanancias import HistoryGananciasCreate
from schemas.loan_schema import LoanCreate, PaymentHistoryItem
from bson import ObjectId
from datetime import datetime, timedelta
from calendar import calendar, monthrange

async def create_loan(loan_data: LoanCreate):
    db = get_db()
    loans_collection = db["loans"]
    clients_collection = db["clients"]
    accounts_collection = db["acounts"]
    history_capital_collection = db["historyCapital"]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")


    # Calcular interés del 15%
    interest = round(loan_data.total_loan * 0.15, 2)

    # Crear documento de deuda
    loan_dict = loan_data.dict()
    loan_dict["client_id"] = ObjectId(loan_data.client_id)
    loan_dict["name"] = loan_data.name
    loan_dict["total_loan"] = loan_data.total_loan
    loan_dict["interest"] = interest
    loan_dict["payment_amount"] = loan_data.payment_amount
    # loan_dict["creation_date"] = datetime.utcnow()
    loan_dict["status"] = "pendiente"
    loan_dict["history"] = []

    result = await loans_collection.insert_one(loan_dict)

    await accounts_collection.update_one({}, {
        "$inc": {
            "capital": -loan_data.total_loan,
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=loan_data.total_loan,
        state="prestamo",
        client_name=loan_data.name 
    )

    await history_capital_collection.insert_one(history_record.dict())

    loan_dict["_id"] = str(result.inserted_id)
    loan_dict["client_id"] = str(loan_dict["client_id"])

    return loan_dict

async def update_loan(loan_data: LoanCreate):
    print('actualizar prestamo', loan_data)
    db = get_db()
    loans_collection = db["loans"]
    clients_collection = db["clients"]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({"client_id": ObjectId(loan_data.client_id)})
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")
    
    # Calcular interés del 15%
    interest = round(loan_data.total_loan * 0.15, 2)

    await loans_collection.update_one(
        {"client_id": ObjectId(loan_data.client_id)},
        {
            "$set": {
                "total_loan": loan_data.total_loan,
                "interest": interest,
                "payment_amount": 0,
                "status": "pendiente", 
                "creation_date": datetime.utcnow(),
                "due_date": loan_data.due_date,
                "interest10": True
            },
        }
    )

    updated_loan = await loans_collection.find_one({"client_id": ObjectId(loan_data.client_id)})

    # antes de retornar hay que convertis de _id a string
    updated_loan["_id"] = str(updated_loan["_id"])
    updated_loan["client_id"] = str(updated_loan["client_id"])

    return {
        "message": "Préstamo actualizado exitosamente",
        "loan": updated_loan
    }


async def get_loan_by_client_id(client_id: str):
    db = get_db()
    loans_collection = db["loans"]

    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="No se encontró préstamo para este cliente")

    loan["_id"] = str(loan["_id"])
    loan["client_id"] = str(loan["client_id"])

    return loan


async def update_interest_payment(client_id: str, paid_interest: float):
    db = get_db()
    loans_collection = db["loans"]
    accounts_collection = db['accounts']
    history_ganancias_collection = db['historyGanancias']

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

    # sumar el interes a las ganancias
    await accounts_collection.update_one(
        {},  # Sin filtro → actualiza el unico documento, solo si hay un solo documento
        {
            "$inc": {
                "ganancias": paid_interest
            }
        }
    )

     # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=paid_interest,
        state="interes",
        client_name=loan["name"] 
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    return {"message": message, "new_due_date": new_due_date_str, "status": status}
 

async def update_payment(client_id: str, payment_amount: float):
    db = get_db()
    loans_collection = db["loans"]
    accounts_collection = db["acounts"]
    history_capital_collection = db["historyCapital"]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    current_due_date_str = loan.get("due_date")
    current_status = loan.get("status")

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
    loan_history[last_index]["total_loan"] = loan["total_loan"] 
    loan_history[last_index]["paymentAmount"] = payment_amount
    loan_history[last_index]["date"] = datetime.utcnow()
    loan_history[last_index]["status"] = 'Deuda completa pagada' if new_total_loan == 0 else current_status

    await loans_collection.update_one(
        {"client_id": ObjectId(client_id)},
        {
            "$set": {
                "total_loan": new_total_loan,
                "interest": interest,
                "status" : 'Deuda completa pagada' if new_total_loan == 0 else current_status,
                "payment_amount": 0 if new_total_loan == 0 else payment_amount,
                "history": loan_history,
            }
        }
    )

    await accounts_collection.update_one({}, {
        "$inc": {
            "capital": payment_amount,
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=payment_amount,
        state="pago  completado" if new_total_loan == 0 else "pago",
        client_name= loan["name"]
    )
    
    await history_capital_collection.insert_one(history_record.dict())

    return {
        "message": "Payment and history updated successfully",
        "total_loan": new_total_loan,
        "interest": interest,
        "history": loan_history,
        "status": 'Deuda completa pagada' if new_total_loan == 0 else current_status
    }

async def update_full_payment(client_id: str):
    db = get_db()
    loans_collection = db["loans"]
    accounts_collection = db["acounts"]
    history_capital_collection = db["historyCapital"]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    # Actualizar loan
    await loans_collection.update_one(
        {"client_id": ObjectId(client_id)},
        {
            "$set": {
                "status": "Deuda completa pagada", 
                "interest": 0,
                "total_loan": 0,
            },
            "$push": {
                "history": {
                    "date": datetime.utcnow(),
                    "total_loan": loan["total_loan"],
                    "status": "Deuda completa pagada",
                    "due_date": loan['due_date'],
                    "interestPayment": loan["total_loan"] * 0.1,
                    "paymentAmount": loan["total_loan"]
                }
            }
        }
    )

    await accounts_collection.update_one({}, {
        "$inc": {
            "capital": loan["total_loan"],
            "ganancias": loan["total_loan"] * 0.1
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=loan["total_loan"],
        state="pago todo",
        client_name= loan["name"]
    )
    
    await history_capital_collection.insert_one(history_record.dict())

    updated_loan = await loans_collection.find_one({"client_id": ObjectId(client_id)})

    return {
        "message": "Pago procesado exitoso", 
        "status": "Deuda completa pagada", 
        "history": updated_loan['history']
    }

async def get_pending_loans_with_total_interest(): 
    
    db = get_db()
    loans_collection = db["loans"]

    # todos los préstamos con estado 'pendiente'
    pending_loans_cursor = loans_collection.find({"status": "pendiente"})
    pending_loans = await pending_loans_cursor.to_list(length=None)

    total_loans_cursor = loans_collection.find({})
    total_loans = await total_loans_cursor.to_list(length=None)

    if not pending_loans:
        raise HTTPException(status_code=404, detail="No hay préstamos pendientes")

    #suma total de intereses de los préstamos
    total_interest = sum(loan.get("interest", 0) for loan in pending_loans)

    #suma total de todos los prestamos 
    total_loan = sum(loan.get("total_loan", 0) for loan in total_loans)

    # Convertir ObjectId a string para cada documento
    for loan in pending_loans:
        loan["_id"] = str(loan["_id"])
        loan["client_id"] = str(loan["client_id"])

    return {
        "total_loan": round(total_loan, 2),
        "total_interest": round(total_interest, 2),
        "pending_loans": pending_loans
    }

#controller para actualizar los datos en loans diariamente


# Función principal
async def update_loans_status():

    db = get_db()
    loans_collection = db["loans"]
    print(f"[{datetime.now()}] Ejecutando actualización de préstamos...")

    async for loan in loans_collection.find({}):
        loan_id = loan["_id"]
        status = loan["status"]
        total_loan = loan["total_loan"]
        due_date_str = loan["due_date"]  # "2025-07-20"
        day_count = loan.get("day")
        interest10 = loan.get("interest10", False)
        creation_date = loan.get("creation_date")
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        today = datetime.utcnow().date()

        # pendiente
        if status == "pendiente":
            day_count -= 1
            updates = {"day": day_count}

            # ✅ Verificar si interest10 sigue activo y han pasado 16 días desde creation_date
            if interest10 and creation_date:
                creation_date_dt = creation_date.date() if isinstance(creation_date, datetime) else datetime.strptime(creation_date, "%Y-%m-%dT%H:%M:%S.%f").date()
                days_passed = (today - creation_date_dt).days
                if days_passed >= 16:
                    updates["interest10"] = False

            # ✅ Si ya pasó la fecha de pago
            if today > due_date:
                updates.update({
                    "status": "En mora",
                    "interest": round(total_loan * 0.18, 2),
                    "day": 5
                })

            # ✅ Solo un update_one al final
            await loans_collection.update_one(
                {"_id": ObjectId(loan_id)},
                {"$set": updates}
            )

        # Si está en mora
        elif status == "En mora":
            if day_count <= 0:
                # Nueva fecha de pago
                new_due_date = due_date + timedelta(days=calendar.monthrange(today.year, today.month)[1])
                new_due_date_str = new_due_date.strftime("%Y-%m-%d")

                # Sumar nuevo interés
                new_interest = loan["interest"] + round(total_loan * 0.15, 2)

                # Calcular nuevos días
                new_day_count = (new_due_date - today).days

                await loans_collection.update_one(
                    {"_id": ObjectId(loan_id)},
                    {"$set": {
                        "due_date": new_due_date_str,
                        "interest": new_interest,
                        "day": new_day_count
                    }}
                )
            else:
                # Resta días igual que en pendiente
                await loans_collection.update_one(
                    {"_id": ObjectId(loan_id)},
                    {"$set": {"day": day_count - 1}}
                )