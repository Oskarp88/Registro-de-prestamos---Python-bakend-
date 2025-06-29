from fastapi import HTTPException
from database.connection import database
from schemas.historyCapital import HistoryCapitalCreate
from schemas.historyGanancias import HistoryGananciasCreate
from schemas.loan_schema import LoanCreate
from bson import ObjectId
from datetime import datetime, timedelta
from calendar import calendar, monthrange

from schemas.notifications import Notifications
from utils.format_currency_value import format_currency_value
from utils.constants import Constants
from websocket_manager.events import notify_latest_notifications

async def create_loan(loan_data: LoanCreate):
    db = database
    loans_collection = db[Constants.LOANS]
    clients_collection = db[Constants.CLIENTS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]
    notifications_collection = db[Constants.NOTIFICATIONS]

    # Verificar si el cliente existe
    client = await clients_collection.find_one({"_id": ObjectId(loan_data.client_id)})
    if not client:
        raise HTTPException(status_code=400, detail="El préstamo no puede ser creado")

    # Obtener fecha actual
    today = datetime.utcnow().date()
    current_day = today.day
    _, last_day_of_month = monthrange(today.year, today.month)

    # Calcular días restantes del mes
    new_day_count = last_day_of_month - current_day

    # Calcular interés
    if current_day >= 28:  # 28, 29, 30 o 31
        interest = round(loan_data.total_loan * 0.15, 2)
    else:
        interest = round((loan_data.total_loan * 0.15 / 30) * (30 - current_day), 2)

    # Validar fecha de vencimiento
    due_date = datetime.strptime(loan_data.due_date, "%Y-%m-%d").date()
    if due_date < today:
        raise HTTPException(status_code=400, detail="La fecha de vencimiento no puede estar en el pasado.")

    # Crear documento de deuda
    loan_dict = loan_data.dict()
    loan_dict[Constants.CLIENT_ID] = ObjectId(loan_data.client_id)
    loan_dict[Constants.NAME] = loan_data.name
    loan_dict[Constants.TOTAL_LOAN] = loan_data.total_loan
    loan_dict[Constants.TOTAL_LOAN_HISTORY] = loan_data.total_loan
    loan_dict[Constants.TOTAL_INTEREST_HISTORY] = 0
    loan_dict[Constants.INTEREST] = interest
    loan_dict[Constants.PAYMENT_AMOUNT] = loan_data.payment_amount
    loan_dict[Constants.STATUS] = Constants.PENDIENTE
    loan_dict[Constants.DAY] = new_day_count
    loan_dict[Constants.HISTORY] = []

    result = await loans_collection.insert_one(loan_dict)

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: -loan_data.total_loan,
        }
    })

    # Crear historial
    history_record = HistoryCapitalCreate(
        amount=loan_data.total_loan,
        state=Constants.PRESTAMO,
        client_name=loan_data.name 
    )
    await history_capital_collection.insert_one(history_record.dict())

    # Crear notificación
    loan_dict["_id"] = str(result.inserted_id)
    loan_dict[Constants.CLIENT_ID] = str(loan_dict[Constants.CLIENT_ID])

    notifications_record = Notifications(
        message=f"Se ha otorgado al cliente {loan_data.name} un préstamo por un monto de {format_currency_value(loan_data.total_loan)}.",
        client_id=loan_data.client_id
    )

    await notifications_collection.insert_one(notifications_record.dict())
    await notify_latest_notifications()

    return loan_dict
  
async def update_loan(loan_data: LoanCreate):
    db = database
    loans_collection = db[Constants.LOANS]
    clients_collection = db[Constants.CLIENTS]
    notifications_collection = db[Constants.NOTIFICATIONS]

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

    due_date = datetime.strptime(loan_data.due_date, "%Y-%m-%d").date()
    today = datetime.utcnow().date()

    if due_date < today:
        raise HTTPException(status_code=400, detail="La fecha de vencimiento no puede estar en el pasado.")

    new_day_count = (due_date - today).days

    await loans_collection.update_one(
        {Constants.CLIENT_ID: ObjectId(loan_data.client_id)},
        {
            "$inc": {
                Constants.TOTAL_LOAN_HISTORY: loan_data.total_loan
            },
            "$set": {
                Constants.TOTAL_LOAN: loan_data.total_loan,
                Constants.TOTAL_INTEREST_HISTORY: loan[Constants.TOTAL_INTEREST_HISTORY],
                Constants.INTEREST: interest,
                Constants.PAYMENT_AMOUNT: 0,
                Constants.STATUS: Constants.PENDIENTE, 
                Constants.CREATION_DATE: datetime.utcnow(),
                Constants.DUE_DATE: loan_data.due_date,
                Constants.INTEREST_10: True,
                Constants.DAY: new_day_count
            },
        }
    )

    updated_loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(loan_data.client_id)})

    # antes de retornar hay que convertis de _id a string
    updated_loan["_id"] = str(updated_loan["_id"])
    updated_loan[Constants.CLIENT_ID] = str(updated_loan[Constants.CLIENT_ID])

    notifications_record = Notifications(
        message=(
            f"Se ha otorgado al cliente {loan_data.name} un préstamo por un monto de {format_currency_value(loan_data.total_loan)}."
        ),
        client_id=loan_data.client_id
    )

    await notifications_collection.insert_one(notifications_record.dict())
    await notify_latest_notifications()

    return {
        Constants.MESSAGE: "Préstamo actualizado exitosamente",
        Constants.LOAN: updated_loan
    }


async def get_loan_by_client_id(client_id: str):
    db = database
    loans_collection = db[Constants.LOANS]

    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="No se encontró préstamo para este cliente")

    loan["_id"] = str(loan["_id"])
    loan[Constants.CLIENT_ID] = str(loan[Constants.CLIENT_ID])

    return loan

async def get_all_loan_client():
    db = database
    loans_collection = db[Constants.LOANS]

    cursor = loans_collection.find({}) 

    loanList = []
    async for loan in cursor:
        if loan[Constants.TOTAL_LOAN] != 0:
            loan["_id"] = str(loan["_id"])
            loan[Constants.CLIENT_ID] = str(loan[Constants.CLIENT_ID])
            loanList.append(loan)

    if not loanList:
        raise HTTPException(status_code=404, detail="No se encontraron préstamos.")

    return loanList



async def update_interest_payment(client_id: str, paid_interest: float):
    db = database
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_ganancias_collection = db[Constants.HISTORY_CAPITAL]
    notifications_collection = db[Constants.NOTIFICATIONS]

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
                Constants.TOTAL_INTEREST_HISTORY: loan[Constants.TOTAL_INTEREST_HISTORY] + paid_interest,
                Constants.DUE_DATE: new_due_date_str,
                Constants.INTEREST_10: False
            },
            "$push": {
                Constants.HISTORY: {
                    Constants.TOTAL_LOAN: loan[Constants.TOTAL_LOAN],
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
                Constants.GANANCIAS: paid_interest,
                Constants.HISTORY_INTEREST: paid_interest
            }
        }
    )

     # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=paid_interest,
        state= Constants.INTEREST,
        client_name=loan[Constants.NAME] 
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    notifications_record = Notifications(
        message=(
            f"El cliente {loan[Constants.NAME]} ha realizado el pago del interés correspondiente por un monto de {format_currency_value(paid_interest)}. "
            f"La próxima fecha de pago de interés será el {new_due_date_str}."
        ),
        client_id=client_id
    )

    await notifications_collection.insert_one(notifications_record.dict())
    await notify_latest_notifications()

    return {
        Constants.MESSAGE: message, 
        Constants.NEW_DUE_DATE: new_due_date_str, 
        Constants.STATUS: status
    }
 

async def update_payment(client_id: str, payment_amount: float):
    db = database
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]
    notifications_collection = db[Constants.NOTIFICATIONS]


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
                    Constants.TOTAL_LOAN: loan[Constants.TOTAL_LOAN],
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

    if new_total_loan == 0:
        message = (
            f"El cliente {loan[Constants.NAME]} ha realizado un abono de {format_currency_value(payment_amount)} "
            f"y ha completado el pago total de su deuda."
        )
    else:
        message = (
            f"El cliente {loan[Constants.NAME]} ha realizado un abono de {format_currency_value(payment_amount)} "
            f"al saldo pendiente de su deuda."
        )

    notifications_record = Notifications(
        message=message,
        client_id=client_id
    )
    
    await notifications_collection.insert_one(notifications_record.dict())
    await notify_latest_notifications()

    return {
        Constants.MESSAGE: "Payment and history updated successfully",
        Constants.TOTAL_LOAN: new_total_loan,
        Constants.INTEREST: interest,
        Constants.HISTORY: updated_loan[Constants.HISTORY],
        Constants.STATUS: Constants.DEUDA_FINALIZADA if new_total_loan == 0 else current_status
    }
  
async def update_full_payment(client_id: str):
    db = database
    loans_collection = db[Constants.LOANS]
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]
    notifications_collection = db[Constants.NOTIFICATIONS]

    # Verificar si existe préstamo
    loan = await loans_collection.find_one({Constants.CLIENT_ID: ObjectId(client_id)})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for this client")
    
    interest_payment = loan[Constants.TOTAL_LOAN] * 0.1
    # Actualizar loan
    await loans_collection.update_one(
        {Constants.CLIENT_ID: ObjectId(client_id)},
        {
            "$inc":{
                Constants.TOTAL_INTEREST_HISTORY: interest_payment
            },
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
                    Constants.INTEREST_PAYMENT: interest_payment,
                    Constants.AMOUNT_PAYMENT: loan[Constants.TOTAL_LOAN]
                }
            }
        }
    )
      
    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: loan[Constants.TOTAL_LOAN],
            Constants.GANANCIAS: interest_payment,
            Constants.HISTORY_INTEREST: interest_payment,
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

    notifications_record = Notifications(
        message=(
            f"El cliente {loan[Constants.NAME]} aprovechó el período de los primeros 15 días y saldó la totalidad de su deuda "
            f"con un interés preferencial del 10%. Pagó {format_currency_value(loan[Constants.TOTAL_LOAN])} de capital "
            f"más {format_currency_value(loan[Constants.TOTAL_LOAN] * 0.1)} de interés."
        ),
        client_id=client_id
    )

    await notifications_collection.insert_one(notifications_record.dict())
    await notify_latest_notifications()

    return {
        Constants.MESSAGE: "Pago procesado exitoso", 
        Constants.STATUS: Constants.DEUDA_COMPLETA_PAGADA, 
        Constants.HISTORY: updated_loan[Constants.HISTORY],
        Constants.INTEREST_PAYMENT: interest_payment,
        Constants.TOTAL_LOAN: loan[Constants.TOTAL_LOAN]
    }

async def get_pending_loans_with_total_interest(): 
    
    db = database
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
        Constants.PENDING_LOANS: pending_loans,
    }

#controller para actualizar los datos en loans diariamente


# Función principal
async def update_loans_status():

    db = database
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
                        message=f"El cliente {loan_name} ha superado los primeros 15 días desde la fecha de otorgamiento del préstamo. A partir de este momento, ya no aplica el interés preferencial del 10%.",
                        client_id=loan_client_id
                    )
                    await notifications_collection.insert_one(notifications_record.dict())
                    await notify_latest_notifications()
                if days_passed >= 21:
                    new_interest = round(loan_interest + (total_loan * 0.03), 2)
                    updates.update({
                        Constants.INTEREST: new_interest,
                        Constants.DAY: 5
                    })                
                    notifications_record = Notifications(
                        message=(
                            f"El cliente {loan_name} ha alcanzado los 20 días sin realizar el pago del interés. "
                            f"Como resultado, la tasa de interés ha aumentado al 18%. El monto a pagar por concepto de interés es de {format_currency_value(total_loan * 0.18)}."
                        ),
                        client_id=loan_client_id
                    )   
                    await notifications_collection.insert_one(notifications_record.dict())
                    await notify_latest_notifications()
            # ✅ Si ya pasó la fecha de pago
            if today > due_date:
                updates.update({
                    Constants.STATUS: Constants.EN_MORA,
                    Constants.DAY: 5
                })

                notifications_record = Notifications(
                    message=(
                        f"El cliente {loan_name} ha incurrido en mora al no realizar el pago del interés correspondiente, "
                        f"por un monto de {format_currency_value(loan_interest)}. "
                        f"Cuenta con un plazo de 5 días a partir de hoy para regularizar su situación."
                    ),
                    client_id=loan_client_id
                )
                await notifications_collection.insert_one(notifications_record.dict())
                await notify_latest_notifications()
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

                notifications_record = Notifications(
                    message=(
                        f"El cliente {loan_name} no realizó el pago del interés de {format_currency_value(loan_interest)} "
                        f"dentro del plazo adicional de 5 días. Este monto ha sido acumulado al nuevo interés, resultando en un total a pagar "
                        f"de {format_currency_value(new_interest)}. La nueva fecha límite para realizar el pago es {new_due_date}."
                    ),
                    client_id=loan_client_id
                )
                await notifications_collection.insert_one(notifications_record.dict())
                await notify_latest_notifications()
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
                    message=(
                        f"El cliente {loan_name} continúa en estado de mora. Le restan {day_count - 1} días para realizar el pago del interés "
                        f"correspondiente, por un monto de {format_currency_value(loan_interest)}."
                    ),
                    client_id=loan_client_id
                )
                await notifications_collection.insert_one(notifications_record.dict())
                await notify_latest_notifications()