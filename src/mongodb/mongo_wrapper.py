# type: ignore

from bson.objectid import ObjectId
from pymongo import MongoClient
from typing import Any, Optional

import logging


class MongoDB:
    _logger = logging.getLogger(__name__)

    __CONNECTION_STRING__ = "{prefix}://{username}:{password}@{host}?retryWrites={retryWrites}&w={writeConcern}"

    def __init__(self,
                 host: str,
                 username: str,
                 password: str,
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

    def insert(self, collection_name: str, documents: list[Any]) -> list[ObjectId]:
        if not documents:
            self._logger.info('No documents to insert')
            return []
        
        collection = self.get_collection(collection_name)
        
        if len(documents) == 1:
            self._logger.info(f'Inserting 1 document into {collection_name}')
            result = collection.insert_one(documents[0])
            return [result.inserted_id]
        
        self._logger.info(
            f'Inserting {len(documents)} documents into {collection_name}')
        result = collection.insert_many(documents)
        return result.inserted_ids
    
    def find(self,
             collection_name: str,
             filter: Optional[dict[str, Any]] = None,
             projection: Optional[dict[str, Any]] = None,
             sort: Optional[dict[str, Any]] = None,
             limit: Optional[int] = None) -> list[Any]:
        limit = limit or 20
        self._logger.info(f'Finding documents in {collection_name}')
        self._logger.info(f'filter: {filter}')
        self._logger.info(f'projection: {projection}')
        self._logger.info(f'sort: {sort}, limit: {limit}')
        collection = self.get_collection(collection_name)
        result_cursor = collection.find(
            filter=filter,
            projection=projection,
            sort=sort,
            limit=limit)
        return [document for document in result_cursor]
