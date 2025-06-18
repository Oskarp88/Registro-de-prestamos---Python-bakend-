import motor.motor_asyncio
from dotenv import load_dotenv
import os

from utils.constants import Constants

load_dotenv()

MONGO_URL = os.getenv(Constants.MONGO_URL)
DATABASE_NAME = os.getenv(Constants.DATABASE_NAME)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client[DATABASE_NAME]

def get_db():
    return database
