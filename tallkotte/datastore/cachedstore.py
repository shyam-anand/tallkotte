from .mongodb.mongo_wrapper import MongoDB, get_mongo
from .mongodb.mongo_query import MongoQuery
from .redisdb.redisdb import get_redis

import logging

from typing import (
    Any, Callable, Generic, Mapping, Optional, TypeVar, Union
)

import json

T = TypeVar('T', bound=Mapping[str, Any])
RedisResult = Union[dict[str, Any], list[dict[str, Any]]]


class Cache(Generic[T]):

    _log = logging.getLogger(__name__)
    _redis = get_redis()

    def __init__(self, key_prefix: str) -> None:
        self._key_prefix = key_prefix

    def _cache_key(self, key: str) -> str:
        return f'{self._key_prefix}:{key}'

    def get(self, key: str) -> Optional[RedisResult]:
        result = self._redis.read(self._cache_key(key))
        if result:
            return json.loads(result)

    def put(self, key: str, value: T | list[T]) -> None:
        def serialize(value: T | list[T]) -> str:
            def delete_object_id(obj: T) -> dict[str, Any]:
                return {
                    key: val
                    for key, val in obj.items()
                    if key != '_id'
                }

            if isinstance(value, list):
                values = [
                    delete_object_id(item)
                    for item in value
                ]
                return json.dumps(values)
            else:
                return json.dumps(delete_object_id(value))

        cache_key = self._cache_key(key)
        cache_data = serialize(value)
        self._log.info(f'cache write: {cache_key} -> {cache_data}')
        self._redis.write(cache_key, cache_data)


class CachedStore(Generic[T]):

    _log = logging.getLogger(__name__)

    def __init__(
            self,
            collection: str,
            convert: Callable[[Mapping[str, Any]], T],
            id_mapper: Callable[[T], str] = lambda t_obj: t_obj['id']) -> None:
        if not collection:
            raise ValueError('key_prefix is required')

        self._collection = collection
        self._convert = convert
        self._id_mapper = id_mapper

        self._mongo: MongoDB[T] = get_mongo()
        self._cache = Cache[T](self._collection)

    def _convert_to_type(self, value: RedisResult) -> T | list[T]:
        if isinstance(value, list):
            return [self._convert(item) for item in value]

        return self._convert(value)

    def read(self,
             key: str,
             on_miss: MongoQuery) -> Optional[list[T]] | Optional[T]:
        cached_result = self._cache.get(key)
        if cached_result:
            self._log.info(f'cache hit: {key} -> {cached_result}')
            if isinstance(cached_result, list):
                return [self._convert(item) for item in cached_result]
            return self._convert(cached_result)

        self._log.info(f'cache miss: {key}')
        db_result = self._mongo.find(
            self._collection, **on_miss)
        if db_result:
            self._log.info(f'DB hit: {key}')
            result = [self._convert(result) for result in db_result]
            self._cache.put(key, result)
            self._log.info(f'cache write: {key}')
            return result

        self._log.info(f'No result for: {key}')

    def write(self, key: str, values: list[T]) -> list[str]:
        object_ids = self._mongo.insert(self._collection, values)
        self._cache.put(key, values)
        return [str(id) for id in object_ids]

    def write_one(self, value: T, key: Optional[str] = None) -> str:
        key = key or self._id_mapper(value)
        object_id = self._mongo.insert_one(self._collection, value)
        self._cache.put(key, value)
        return str(object_id)

    def upsert(self, key: str, value: T, query: MongoQuery) -> str:
        """Does an upsert operation.

        The query is used to determine if the document exists. If it does, it
        is updated, otherwise it is inserted.

        The cached value is updated always.
        """
        upsert_id = self._mongo.upsert(
            self._collection, query['filter'], value)
        self._cache.put(key, value)
        upsert_id_str = str(upsert_id)
        self._log.info(f'upsert: {key} -> {upsert_id_str}')
        return upsert_id_str
