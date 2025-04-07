import motor.motor_asyncio


# "mongodb://root:example@localhost:27017/?authSource=admin"

client = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb://root:password@localhost:27017/?authSource=admin"
)

database = client.mokitul
