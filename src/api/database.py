import motor.motor_asyncio
import os

from api.settings import MONGO_DETAILS


#"mongodb://root:example@localhost:27017/?authSource=admin"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.mokitul
