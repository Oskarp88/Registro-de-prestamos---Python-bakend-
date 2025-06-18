from fastapi import HTTPException
from database.connection import get_db
from schemas.historyCapital import HistoryCapitalCreate
from schemas.historyGanancias import HistoryGananciasCreate
from schemas.loan_schema import LoanCreate, PaymentHistoryItem
from bson import ObjectId
from datetime import datetime, timedelta
from calendar import calendar, monthrange

from schemas.notifications import Notifications
from utils import format_currency_value
from utils.constants import Constants

async def create_loan(loan_data: LoanCreate):
    db = get_db()
    loans_collection = db[Constants.LOANS]
    clients_collection = db[Constants.CLIENTS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")


    # Calcular interés del 15%
    interest = round(loan_data.total_loan * 0.15, 2)

    # Crear documento de deuda
    loan_dict = loan_data.dict()
    loan_dict[Constants.CLIENT_ID] = ObjectId(loan_data.client_id)
    loan_dict[Constants.NAME] = loan_data.name
    loan_dict[Constants.TOTAL_LOAN] = loan_data.total_loan
    loan_dict[Constants.INTEREST] = interest
    loan_dict[Constants.PAYMENT_AMOUNT] = loan_data.payment_amount
    # loan_dict["creation_date"] = datetime.utcnow()
    loan_dict[Constants.STATUS] = Constants.PENDIENTE
    loan_dict[Constants.HISTORY] = []

    result = await loans_collection.insert_one(loan_dict)

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: -loan_data.total_loan,
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=loan_data.total_loan,
        state= Constants.PRESTAMO,
        client_name=loan_data.name 
    )

    await history_capital_collection.insert_one(history_record.dict())

    loan_dict["_id"] = str(result.inserted_id)
    loan_dict[Constants.CLIENT_ID] = str(loan_dict[Constants.CLIENT_ID])

    return loan_dict

async def update_loan(loan_data: LoanCreate):
    db = get_db()
    loans_collection = db[Constants.LOANS]
    clients_collection = db[Constants.CLIENTS]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(loan_data.client_id)})
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")
    
    # Calcular interés del 15%
    interest = round(loan_data.total_loan * 0.15, 2)

    await loans_collection.update_one(
        {Constants.CLIENT_ID: ObjectId(loan_data.client_id)},
        {
            "$set": {
                Constants.TOTAL_LOAN: loan_data.total_loan,
                Constants.INTEREST: interest,
                Constants.PAYMENT_AMOUNT: 0,
                Constants.STATUS: Constants.PENDIENTE, 
                Constants.CREATION_DATE: datetime.utcnow(),
                Constants.DUE_DATE: loan_data.due_date,
                Constants.INTEREST_10: True
            },
        }
    )

    updated_loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(loan_data.client_id)})

    # antes de retornar hay que convertis de _id a string
    updated_loan["_id"] = str(updated_loan["_id"])
    updated_loan[Constants.CLIENT_ID] = str(updated_loan[Constants.CLIENT_ID])

    return {
        Constants.MESSAGE: "Préstamo actualizado exitosamente",
        Constants.LOAN: updated_loan
    }


async def get_loan_by_client_id(client_id: str):
    db = get_db()
    loans_collection = db[Constants.LOANS]

    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="No se encontró préstamo para este cliente")

    loan["_id"] = str(loan["_id"])
    loan[Constants.CLIENT_ID] = str(loan[Constants.CLIENT_ID])

    return loan


async def update_interest_payment(client_id: str, paid_interest: float):
    db = get_db()
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_ganancias_collection = db[Constants.HISTORY_CAPITAL]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    current_interest = loan.get(Constants.INTEREST, 0)
    current_due_date_str = loan.get(Constants.DUE_DATE)

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
        status = Constants.PENDIENTE
        message = "Interes pagado parcialmente"
    else:
        status = Constants.INTERES_PAGADO
        message = Constants.INTERES_PAGADO

    # Actualizar loan
    await loans_collection.update_one(
        {"client_id": ObjectId(client_id)},
        {
            "$set": {
                Constants.STATUS: status, 
                Constants.DUE_DATE: new_due_date_str
            },
            "$push": {
                Constants.HISTORY: {
                    Constants.DATE: datetime.utcnow(),
                    Constants.STATUS: message,
                    Constants.DUE_DATE: current_due_date_str,
                    Constants.INTEREST_PAYMENT: paid_interest,
                    Constants.AMOUNT_PAYMENT: 0
                }
            }
        }
    )

    # sumar el interes a las ganancias
    await accounts_collection.update_one(
        {},  # Sin filtro → actualiza el unico documento, solo si hay un solo documento
        {
            "$inc": {
                Constants.GANANCIAS: paid_interest
            }
        }
    )

     # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=paid_interest,
        state=Constants.INTEREST,
        client_name=loan[Constants.NAME] 
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    return {
        Constants.MESSAGE: message, 
        Constants.NEW_DUE_DATE: new_due_date_str, 
        Constants.STATUS: status
    }
 

async def update_payment(client_id: str, payment_amount: float):
    db = get_db()
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    current_due_date_str = loan.get(Constants.DUE_DATE)
    current_status = loan.get(Constants.STATUS)

    if not current_due_date_str:
        raise HTTPException(status_code=400, detail="Loan has no due date set")

    # Calcula el nuevo total_loan
    new_total_loan = loan[Constants.TOTAL_LOAN] - payment_amount

     # Calcular interés del 15%
    interest = round( new_total_loan * 0.15, 2)

    await loans_collection.update_one(
        {Constants.CLIENT_ID: ObjectId(client_id)},
        {
            "$set": {
                Constants.TOTAL_LOAN: new_total_loan,
                Constants.INTEREST: interest,
                Constants.STATUS: Constants.DEUDA_FINALIZADA if new_total_loan == 0 else current_status,
                Constants.PAYMENT_AMOUNT: 0 if new_total_loan == 0 else payment_amount,
            },
            "$push": {
                Constants.HISTORY: {
                    Constants.TOTAL_LOAN: new_total_loan,
                    Constants.DATE: datetime.utcnow(),
                    Constants.STATUS: Constants.DEUDA_FINALIZADA if new_total_loan == 0 else Constants.ABONO,
                    Constants.DUE_DATE: current_due_date_str,
                    Constants.INTEREST_PAYMENT: interest,
                    Constants.AMOUNT_PAYMENT: payment_amount
                }
            }
        
        }
    )

    updated_loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: payment_amount,
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=payment_amount,
        state= Constants.DEUDA_FINALIZADA if new_total_loan == 0 else Constants.PAGO,
        client_name= loan[Constants.NAME]
    )
    
    await history_capital_collection.insert_one(history_record.dict())

    return {
        Constants.MESSAGE: "Payment and history updated successfully",
        Constants.TOTAL_LOAN: new_total_loan,
        Constants.INTEREST: interest,
        Constants.HISTORY: updated_loan[Constants.HISTORY],
        Constants.STATUS: Constants.DEUDA_FINALIZADA if new_total_loan == 0 else current_status
    }
  
async def update_full_payment(client_id: str):
    db = get_db()
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")

    # Actualizar loan
    await loans_collection.update_one(
        {Constants.CLIENT_ID: ObjectId(client_id)},
        {
            "$set": {
                Constants.STATUS: Constants.DEUDA_COMPLETA_PAGADA, 
                Constants.INTEREST: 0,
                Constants.TOTAL_LOAN: 0,
                Constants.PAYMENT_AMOUNT: 0,
            },
            "$push": {
                Constants.HISTORY: {
                    Constants.DATE: datetime.utcnow(),
                    Constants.TOTAL_LOAN: loan[Constants.TOTAL_LOAN],
                    Constants.STATUS: Constants.DEUDA_COMPLETA_PAGADA,
                    Constants.DUE_DATE: loan[Constants.DUE_DATE],
                    Constants.INTEREST_PAYMENT: loan[Constants.TOTAL_LOAN] * 0.1,
                    Constants.AMOUNT_PAYMENT: loan[Constants.TOTAL_LOAN]
                }
            }
        }
    )

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: loan[Constants.TOTAL_LOAN],
            Constants.GANANCIAS: loan[Constants.TOTAL_LOAN] * 0.1
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=loan[Constants.TOTAL_LOAN],
        state=Constants.PAGO_TODO,
        client_name= loan[Constants.NAME]
    )
    
    await history_capital_collection.insert_one(history_record.dict())

    updated_loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    return {
        Constants.MESSAGE: "Pago procesado exitoso", 
        Constants.STATUS: Constants.DEUDA_COMPLETA_PAGADA, 
        Constants.HISTORY: updated_loan[Constants.HISTORY]
    }

async def get_pending_loans_with_total_interest(): 
    
    db = get_db()
    loans_collection = db[Constants.LOANS]

    # todos los préstamos con estado 'pendiente'
    pending_loans_cursor = loans_collection.find({Constants.STATUS: Constants.PENDIENTE})
    pending_loans = await pending_loans_cursor.to_list(length=None)

    total_loans_cursor = loans_collection.find({})
    total_loans = await total_loans_cursor.to_list(length=None)

    if not pending_loans:
        raise HTTPException(status_code=404, detail="No hay préstamos pendientes")

    #suma total de intereses de los préstamos
    total_interest = sum(loan.get(Constants.INTEREST, 0) for loan in pending_loans)

    #suma total de todos los prestamos 
    total_loan = sum(loan.get(Constants.TOTAL_LOAN, 0) for loan in total_loans)

    # Convertir ObjectId a string para cada documento
    for loan in pending_loans:
        loan["_id"] = str(loan["_id"])
        loan[Constants.CLIENT_ID] = str(loan[Constants.CLIENT_ID])

    return {
        Constants.TOTAL_LOAN: round(total_loan, 2),
        Constants.TOTAL_INTEREST: round(total_interest, 2),
        Constants.PENDING_LOANS: pending_loans
    }

#controller para actualizar los datos en loans diariamente


# Función principal
async def update_loans_status():

    db = get_db()
    loans_collection = db[Constants.LOANS]
    notifications_collection = db[Constants.NOTIFICATIONS]
    print(f"[{datetime.now()}] Ejecutando actualización de préstamos...")

    async for loan in loans_collection.find({}):
        loan_id = loan["_id"]
        loan_client_id = loan[Constants.CLIENT_ID]
        loan_name = loan[Constants.NAME]
        loan_interest = loan[Constants.INTEREST]
        status = loan[Constants.STATUS]
        total_loan = loan[Constants.TOTAL_LOAN]
        due_date_str = loan[Constants.DUE_DATE] 
        day_count = loan.get(Constants.DAY)
        interest10 = loan.get(Constants.INTEREST_10, False)
        creation_date = loan.get(Constants.CREATION_DATE)
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        today = datetime.utcnow().date()

        # pendiente
        if status == Constants.PENDIENTE:
            day_count -= 1
            updates = {Constants.DAY: day_count}

            # ✅ Verificar si interest10 sigue activo y han pasado 16 días desde creation_date
            if creation_date:
                creation_date_dt = creation_date.date() if isinstance(creation_date, datetime) else datetime.strptime(creation_date, "%Y-%m-%dT%H:%M:%S.%f").date()
                days_passed = (today - creation_date_dt).days
                if interest10 and days_passed >= 16:
                    updates[Constants.INTEREST_10] = False
                    notifications_record = Notifications(
                        message=f"El cliente {loan_name} ya paso por los primero 15 dias desde que obtuvo el prestamo, por lo tanto ya no aplica el interés del 10%",
                        client_id= loan_client_id  
                    )   
                    await notifications_collection.insert_one(notifications_record.dict())
                if days_passed >= 21:
                    updates.update({
                        Constants.INTEREST: round(total_loan * 0.18, 2),
                        Constants.DAY: 5
                    })                
                    notifications_record = Notifications(
                        message=f"El cliente {loan_name} ya tiene 20 dias y no ha pagado el interes, el interés subio al 18% y tiene que pagar {format_currency_value(total_loan * 0.18)} de interés.",
                        client_id= loan_client_id  
                    )   
                    await notifications_collection.insert_one(notifications_record.dict())
            # ✅ Si ya pasó la fecha de pago
            if today > due_date:
                updates.update({
                    Constants.STATUS: Constants.EN_MORA,
                    Constants.DAY: 5
                })

                notifications_record =  Notifications(
                    message=f"El cliente {loan_name} entro en mora, no ha pagado su interes de {format_currency_value(loan_interest)}, tiene 5 dias apartir de hoy para poder pagar.",
                    client_id= loan_client_id  
                ) 
                await notifications_collection.insert_one(notifications_record.dict())
            # ✅ Solo un update_one al final
            await loans_collection.update_one(
                {"_id": ObjectId(loan_id)},
                {"$set": updates}
            )

        # Si está en mora
        elif status == Constants.EN_MORA:
            if day_count <= 0:
                # Nueva fecha de pago
                new_due_date = due_date + timedelta(days=calendar.monthrange(today.year, today.month)[1])
                new_due_date_str = new_due_date.strftime("%Y-%m-%d")

                # Sumar nuevo interés
                new_interest = loan[Constants.INTEREST] + round(total_loan * 0.15, 2)

                # Calcular nuevos días
                new_day_count = (new_due_date - today).days

                notifications_record = notifications_collection(
                    message=f"El cliente {loan_name} se le vencieron los 5 dias extra y no pago el interes de {format_currency_value(loan_interest)}, ese interes fue sumado al nuevo interes y tendra que pagar el siguiente interes de {format_currency_value(new_interest)} y su nueva fecha limite para pagar es {new_due_date}.",
                    client_name= loan_client_id  
                ) 
                await notifications_collection.insert_one(notifications_record.dict())
                await loans_collection.update_one(
                    {"_id": ObjectId(loan_id)},
                    {"$set": {
                        Constants.DUE_DATE: new_due_date_str,
                        Constants.STATUS: Constants.PENDIENTE,
                        Constants.INTEREST: new_interest,
                        Constants.DAY: new_day_count
                    }}
                )
            else:
                # Resta días igual que en pendiente
                await loans_collection.update_one(
                    {"_id": ObjectId(loan_id)},
                    {"$set": {Constants.DAY: day_count - 1}}
                )

                notifications_record = Notifications(
                    message=f"El cliente {loan_name} sigue en mora, le quedan {day_count - 1} para pagar el interes de {format_currency_value(loan_interest)}.",
                    client_name= loan_client_id  
                ) 
                await notifications_collection.insert_one(notifications_record.dict())