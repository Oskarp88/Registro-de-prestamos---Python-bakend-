import motor.motor_asyncio
import os
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()


from utils.constants import Constants

MONGO_URL = os.getenv(Constants.MONGO_URL)
DATABASE_NAME = os.getenv(Constants.DATABASE_NAME)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client[DATABASE_NAME]

def get_db():
    return database
