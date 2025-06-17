from fastapi import HTTPException
from bson import ObjectId

from database.connection import get_db
from schemas.historyCapital import HistoryCapitalCreate
from schemas.historyGanancias import HistoryGananciasCreate

# Agregar capital
async def add_capital(amount: float):
    db = get_db()
    accounts_collection = db['accounts']
    history_capital_collection = db['historyCapital']

    # Actualizar capital
    result = await accounts_collection.update_one({}, {"$inc": {"capital": amount}})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="No se pudo actualizar capital.")

    new_data = await accounts_collection.find_one({})

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state="deposito",
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

    return {
        "message": "Capital agregado con éxito",
        "capital": new_data['capital'],
        "ganancias": new_data['ganancias']
    }
# Retirar ganancias
async def withdraw_ganancias(amount: float):
    db = get_db()
    accounts_collection = db['accounts']
    history_ganancias_collection = db['historyGanancias']

    account = await accounts_collection.find_one({})
    if account['ganancias'] < amount:
        raise HTTPException(status_code=400, detail="Fondos insuficientes.")
    
    # Crear registro en historial
    history_record = HistoryGananciasCreate(
        amount=amount,
        state="retiro",
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record.dict())

    await accounts_collection.update_one({}, {"$inc": {"ganancias": -amount}})
    new_data = await accounts_collection.find_one({})
    return {
        "message": "Dinero retirado con éxito",
        "ganancias": new_data['ganancias']
    }

# Transferir de capital a ganancias
async def transfer_capital_to_ganancias(amount: float):
    db = get_db()
    accounts_collection = db['accounts']
    history_capital_collection = db['historyCapital']
    history_ganancias_collection = db['historyGanancias']

    account = await accounts_collection.find_one({})
    if account['capital'] < amount:
        raise HTTPException(status_code=400, detail="Fondos insuficientes.")

    await accounts_collection.update_one({}, {
        "$inc": {
            "capital": -amount,
            "ganancias": amount
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state="transferencia a ganancias",
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

      # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=amount,
        state="transferencia a Ganancias",
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    new_data = await accounts_collection.find_one({})
    return {
        "message": "Transferencia realizada",
        "capital": new_data['capital'],
        "ganancias": new_data['ganancias']
    }

# Transferir de ganancias a capital
async def transfer_ganancias_to_capital(amount: float):
    db = get_db()
    accounts_collection = db['accounts']
    history_capital_collection = db['historyCapital']
    history_ganancias_collection = db['historyGanancias']

    account = await accounts_collection.find_one({})
    if account['ganancias'] < amount:
        raise HTTPException(status_code=400, detail="Ganancias insuficientes.")

    await accounts_collection.update_one({}, {
        "$inc": {
            "ganancias": -amount,
            "capital": amount
        }
    })

    # Crear registro en historial
    history_record = HistoryCapitalCreate(
        amount=amount,
        state="transferencia a capital",
        client_name=""  
    )

    await history_capital_collection.insert_one(history_record.dict())

      # Crear registro en historial
    history_record_ganancias = HistoryGananciasCreate(
        amount=amount,
        state="transferencia a capital",
        client_name=""  
    )

    await history_ganancias_collection.insert_one(history_record_ganancias.dict())

    new_data = await accounts_collection.find_one({})
    return {
        "message": "Transferencia realizada",
        "capital": new_data['capital'],
        "ganancias": new_data['ganancias']
    }
