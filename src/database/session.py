from typing import Any, Optional
from api.model import NotFoundException
from bson import ObjectId
from pymongo import MongoClient
import motor.motor_asyncio
from motor.motor_asyncio import (
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
    AsyncIOMotorClient,
)
from pydantic import BaseModel
from typing import Generic, List, TypeVar, Type
from core import Result
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    host: str
    port: str
    database_name: str
    username: str
    password: str


class MongoDatabaseSession:
    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _database = None

    """
    CRUD operations for MongoDB.
    handle the connection to the database.
    """

    def __new__(cls, config: Optional[DatabaseConfig] = None):
        assert config is not None, (
            "Configuration must be provided for the first initialization."
        )
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        else:
            cls._instance._shutdown()
        db_url = cls._build_db_url(config)
        cls._instance._initialize(db_url, config.database_name)
        return cls._instance

    @staticmethod
    def _build_db_url(config: DatabaseConfig) -> str:
        """Build the MongoDB connection URL from the configuration."""
        return (
            f"mongodb://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/?authSource=admin"
        )

    @staticmethod
    def init_database(config: DatabaseConfig):
        MongoDatabaseSession(config)

    @staticmethod
    def get_instance() -> motor.motor_asyncio.AsyncIOMotorDatabase[Any]:
        """Return the MongoDB database instance."""
        assert MongoDatabaseSession._instance is not None, (
            "Database is not initialized."
        )
        return MongoDatabaseSession._instance._database

    def _initialize(self, db_url: str, database_name: str):
        """Initialize the MongoDB client and select the database."""
        self._client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
        self._database = self._client[database_name]

    def _shutdown(self):
        """Initialize the MongoDB client and select the database."""
        assert self._client is not None
        self._client.close()


## Example usage
## if __name__ == "__main__":
##     config = DataBaseConfig(
##         host="localhost",
##         port="27017",
##         database_name="testdb",
##         username="user",
##         password="password",
##     )
##
##     Get the singleton instance
##     db_session_handler = DatabaseSession(config)
##
##     Get the database
##     db = db_session_handler.get_database()
##
##     Example operations
##     collection = db["example_collection"]
##     collection.insert_one({"key": "value"})
##     print(list(collection.find()))


T = TypeVar("T", bound=BaseModel)
ID_ATTRIBUTE_STR = "_id"


class BaseDatabase(Generic[T]):
    _model: Type[T]
    _session: AsyncIOMotorDatabase[Any]
    _collection: AsyncIOMotorCollection[Any]
    _collection_name: str

    def __init__(self, model: Type[T], collection_name: str):
        """
        Initialize the ProjectDatabase with a specific Pydantic model and MongoDB collection.
        """
        self._model = model
        self._session = MongoDatabaseSession.get_instance()
        self._collection = self._session.get_collection(collection_name)
        self._collection_name = collection_name

    async def start(self):
        if self._collection is None:
            await self._session.create_collection(self._collection_name)
            self._collection = self._session.get_collection(self._collection_name)

    async def create(self, obj: T) -> Result[str]:
        """
        Insert a Pydantic model instance into the collection.
        Returns the inserted document's ID.
        """
        try:
            result = await self._collection.insert_one(obj.model_dump())
            if result.acknowledged:
                return Result.Ok(str(result.inserted_id))
            return Result.Err(Exception(f"Could Not Create Object {result}"))
        except Exception as e:
            return Result.Err(e)

    async def get(self, id: str) -> Result[T]:
        """
        Retrieve documents matching the query.
        Returns a list of Pydantic model instances.
        """
        try:
            doc = await self._collection.find_one({ID_ATTRIBUTE_STR: ObjectId(id)})
            if doc:
                return Result.Ok(self._model.model_validate(obj=doc))
            return Result.Err(NotFoundException(f"Object {id} not found"))
        except Exception as e:
            return Result.Err(e)

    async def get_all(self) -> Result[List[T]]:
        """
        Retrieve documents matching the query.
        Returns a list of Pydantic model instances.
        """
        documents: List[T] = []
        try:
            async for doc in self._collection.find():
                documents.append(self._model.model_validate(obj=doc))
            return Result.Ok(documents)
        except Exception as e:
            return Result.Err(e)

    async def update(self, id: str, obj: T) -> Result[None]:
        try:
            result = await self._collection.update_one(
                filter={ID_ATTRIBUTE_STR: ObjectId(id)},
                update={"$set": obj.model_dump()},
            )

            if result.modified_count == 1 or (
                result.raw_result and result.raw_result["ok"] == 1
            ):
                return Result.Ok()
            return Result.Err(NotFoundException(f"Update Failed {result.raw_result}"))
        except Exception as e:
            return Result.Err(e)

    async def delete(self, id: str) -> Result[None]:
        """
        Delete documents matching the query.
        Returns the number of documents deleted.
        """
        try:
            result = await self._collection.delete_one(
                filter={ID_ATTRIBUTE_STR: ObjectId(id)},
            )
            if result.deleted_count == 1:
                return Result.Ok()
            return Result.Err(NotFoundException(f"Failed Deletion {result.raw_result}"))
        except Exception as e:
            return Result.Err(e)

    async def run_query(self, query: dict[str, str]) -> Result[List[T]]:
        documents: List[T] = []
        try:
            async for doc in self._collection.find(query):
                documents.append(self._model.model_validate(obj=doc))
            return Result.Ok(documents)
        except Exception as e:
            return Result.Err(e)
