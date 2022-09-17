from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import conf


async def init_db(app):
    app.mongodb_client = AsyncIOMotorClient(conf.MONGO_URI)
    app.db = app.mongodb_client[conf.DB_NAME]

    asset_index = [("policy_id", DESCENDING), ("name", DESCENDING)]
    await app.db["assets"].create_index(asset_index, unique=True)

    collection_index = [("policy_id", DESCENDING)]
    await app.db["collections"].create_index(collection_index, unique=True)
