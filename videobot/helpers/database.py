import motor.motor_asyncio
from config import Config

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    async def add_user(self, id):
        user = await self.col.find_one({'id': int(id)})
        if not user:
            await self.col.insert_one({'id': int(id)})

    async def get_all_users(self):
        return self.col.find({})

db = Database(Config.MONGO_URL, "VideoBot")
