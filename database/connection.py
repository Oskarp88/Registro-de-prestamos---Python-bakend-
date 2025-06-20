import motor.motor_asyncio
import os

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

from utils.constants import Constants

MONGO_URL = os.getenv(Constants.MONGO_URL)
DATABASE_NAME = os.getenv(Constants.DATABASE_NAME)

# ✅ Agrega logs para verificar que sí se lee correctamente
print("🌐 ENV:", os.getenv("ENV"))
print("🔐 MONGO_URL:", "Present" if MONGO_URL else "Missing")
print("📂 DATABASE_NAME:", DATABASE_NAME)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)

database = client[DATABASE_NAME]

