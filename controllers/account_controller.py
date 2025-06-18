from fastapi import HTTPException
from bson import ObjectId

from database.connection import get_db
from schemas.historyCapital import HistoryCapitalCreate
from schemas.historyGanancias import HistoryGananciasCreate
from utils.constants import Constants

# Agregar capital
async def add_capital(amount: float):
    db = get_db()
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]

    # Actualizar capital
    result = await accounts_collection.update_one({}, {"$inc": {Constants.CAPITAL: amount}})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="No se pudo actualizar capital.")

    new_data = await accounts_collection.find_one({})

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state=Constants.DEPOSITO,
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

    return {
        Constants.MESSAGE: "Capital agregado con éxito",
        Constants.CAPITAL: new_data[Constants.CAPITAL],
        Constants.GANANCIAS: new_data[Constants.GANANCIAS]
    }
# Retirar ganancias
async def withdraw_ganancias(amount: float):
    db = get_db()
    accounts_collection = db[Constants.ACCOUNTS]
    history_ganancias_collection = db[Constants.HISTORY_CAPITAL]

    account = await accounts_collection.find_one({})
    if account[Constants.GANANCIAS] < amount:
        raise HTTPException(status_code=400, detail="Fondos insuficientes.")
    
    # Crear registro en historial
    history_record = HistoryGananciasCreate(
        amount=amount,
        state=Constants.RETIRO,
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record.dict())

    await accounts_collection.update_one({}, {"$inc": {Constants.GANANCIAS: -amount}})
    new_data = await accounts_collection.find_one({})
    return {
        Constants.MESSAGE: "Dinero retirado con éxito",
        Constants.GANANCIAS: new_data[Constants.GANANCIAS]
    }

# Transferir de capital a ganancias
async def transfer_capital_to_ganancias(amount: float):
    db = get_db()
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]
    history_ganancias_collection = db[Constants.HISTORY_GANANCIAS]

    account = await accounts_collection.find_one({})
    if account[Constants.CAPITAL] < amount:
        raise HTTPException(status_code=400, detail="Fondos insuficientes.")

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.CAPITAL: -amount,
            Constants.GANANCIAS: amount
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state=Constants.TRANSFERENCIA_A_GANANCIAS,
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

      # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=amount,
        state=Constants.TRANSFERENCIA_A_GANANCIAS,
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    new_data = await accounts_collection.find_one({})
    return {
        Constants.MESSAGE: "Transferencia realizada",
        Constants.CAPITAL: new_data[Constants.CAPITAL],
        Constants.GANANCIAS: new_data[Constants.GANANCIAS]
    }

# Transferir de ganancias a capital
async def transfer_ganancias_to_capital(amount: float):
    db = get_db()
    accounts_collection = db[Constants.ACCOUNTS]
    history_capital_collection = db[Constants.HISTORY_CAPITAL]
    history_ganancias_collection = db[Constants.HISTORY_GANANCIAS]

    account = await accounts_collection.find_one({})
    if account[Constants.GANANCIAS] < amount:
        raise HTTPException(status_code=400, detail="Ganancias insuficientes.")

    await accounts_collection.update_one({}, {
        "$inc": {
            Constants.GANANCIAS: -amount,
            Constants.CAPITAL: amount
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state=Constants.TRANSFERENCIA_A_CAPITAL,
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

      # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=amount,
        state=Constants.TRANSFERENCIA_A_CAPITAL,
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    new_data = await accounts_collection.find_one({})
    return {
        Constants.MESSAGE: "Transferencia realizada",
        Constants.CAPITAL: new_data[Constants.CAPITAL],
        Constants.GANANCIAS: new_data[Constants.GANANCIAS]
    }
