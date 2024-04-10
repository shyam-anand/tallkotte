from bson.objectid import ObjectId
from flask import current_app, g
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Any, Generic, Mapping, Optional, TypeVar

import logging


T = TypeVar('T', bound=Mapping[str, Any])


class MongoDB(Generic[T]):
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
        prefix = 'mongodb+srv' \
            if connection_string_format == 'srv' else 'mongodb'
        connection_string = self.__CONNECTION_STRING__.format(
            username=username,
            password=password,
            host=host,
            retryWrites=retryWrites,
            writeConcern=writeConcern,
            prefix=prefix)

        self._logger.info(f'Connecting to MongoDB: {connection_string}')
        self._client = MongoClient[T](connection_string)

        server_info = self._client.server_info()
        self._logger.info(f'Connected to MongoDB: {server_info}')

        self._db = self._client[db]

    def list_collections(self) -> list[str]:
        return self._db.list_collection_names()

    def get_collection(self, collection_name: str) -> Collection[T]:
        return self._db[collection_name]

    def insert(self, collection_name: str, documents: list[T]) -> list[ObjectId]:
        if not documents:
            self._logger.info('No documents to insert')
            return []

        collection = self.get_collection(collection_name)

        self._logger.info(
            f'Inserting {len(documents)} documents into {collection_name}')
        result = collection.insert_many(documents)
        return result.inserted_ids

    def insert_one(self, collection_name: str, document: T) -> ObjectId:
        self._logger.info(f'Inserting 1 document into {collection_name}')
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        self._logger.info(f'inserted_id: {result.inserted_id}')
        return result.inserted_id

    def find(self,
             collection_name: str,
             filter: Optional[dict[str, Any]] = None,
             projection: Optional[dict[str, Any]] = None,
             sort: Optional[dict[str, Any]] = None,
             limit: Optional[int] = None) -> list[T]:
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

    def upsert(self,
               collection_name: str,
               filter: dict[str, Any],
               data: dict[str, Any] | Mapping[str, Any]) -> Any:
        collection = self.get_collection(collection_name)
        upsert_result = collection.update_one(
            filter, {'$set': data}, upsert=True)
        return upsert_result.upserted_id


U = TypeVar('U', bound=Mapping[str, Any])


def get_mongo() -> MongoDB[U]:  # type: ignore
    if 'mongodb' not in g:
        g.mongodb = MongoDB[U](
            host=current_app.config['MONGO_HOST'],  # type: ignore
            username=current_app.config['MONGO_USERNAME'],  # type: ignore
            password=current_app.config['MONGO_PASSWORD'],  # type: ignore
            db=current_app.config['MONGO_DATABASE']  # type: ignore
        )

    return g.mongodb
