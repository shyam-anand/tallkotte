# type: ignore

from bson.objectid import ObjectId
from pymongo import MongoClient
from typing import Any, Optional

import logging


class MongoDB:
    _logger = logging.getLogger(__name__)

    __CONNECTION_STRING__ = "{prefix}://{username}:{password}@{host}?retryWrites={retryWrites}&w={writeConcern}"

    def __init__(self,
                 username: str,
                 password: str,
                 host: str,
                 db: str,
                 retryWrites: str = 'true',
                 writeConcern: str = 'majority',
                 connection_string_format: str = 'standard') -> None:
        connection_string = self.__CONNECTION_STRING__.format(username=username,
                                                              password=password,
                                                              host=host,
                                                              retryWrites=retryWrites,
                                                              writeConcern=writeConcern,
                                                              prefix='mongodb+srv' if connection_string_format == 'srv' else 'mongodb')
        self._logger.info(f'Connecting to MongoDB: {connection_string}')
        self._client = MongoClient(connection_string)
        self._db = self._client[db]

        self._logger.info(f'Connected to MongoDB, now using database: {db}')

    def list_collections(self) -> list[str]:
        return self._db.list_collection_names()

    def get_collection(self, collection_name: str) -> MongoClient:
        return self._db[collection_name]

    def insert(self, collection_name: str, document: list[Any]) -> list[ObjectId]:
        collection = self.get_collection(collection_name)
        result = collection.insert_many(document)
        return result.inserted_ids

    def find(self,
             collection_name: str,
             filter: Optional[dict[str, Any]] = None,
             projection: Optional[dict[str, Any]] = None,
             sort: Optional[dict[str, Any]] = None,
             limit: int = 20) -> list[Any]:
        collection = self.get_collection(collection_name)
        result_cursor = collection.find(
            filter=filter,
            projection=projection,
            sort=sort,
            limit=limit)
        return [document for document in result_cursor]
