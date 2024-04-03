from .mongodb.mongo_wrapper import MongoDB, get_mongo
from .mongodb.mongo_query import MongoQuery
from .redisdb.redisdb import get_redis

from typing import (
    Any, Callable, Generic, Mapping, Optional, TypeVar, Union
)

import json

T = TypeVar('T', bound=Mapping[str, Any])
RedisResult = Union[dict[str, Any], list[dict[str, Any]]]


class CachedStore(Generic[T]):

    def __init__(self,
                 collection: str,
                 convert: Callable[[dict[str, Any]], T]):
        if not collection:
            raise ValueError('key_prefix is required')

        self._collection = collection
        self._convert = convert

        self._redis = get_redis()
        self._mongo: MongoDB[T] = get_mongo(T)

    def _cache_key(self, key: str) -> str:
        return f'{self._collection}:{key}'

    def _get(self, key: str) -> Optional[RedisResult]:
        result = self._redis.read(self._cache_key(key))
        if result:
            return json.loads(result)

    def _redis_read(self, key: str) -> Optional[list[T]] | Optional[T]:
        redis_result = self._get(key)
        if not redis_result:
            return None

        if isinstance(redis_result, list):
            return [self._convert(item) for item in redis_result]
        else:
            return self._convert(redis_result)

    def read(self, key: str, on_miss: MongoQuery) -> Optional[list[T]] | Optional[T]:
        cached_result = self._redis_read(key)
        if cached_result:
            return cached_result

        db_result = self._mongo.find(
            self._collection, **on_miss)  # type: ignore
        if db_result:
            result = [self._convert(result) for result in db_result]
            self._redis.write(self._cache_key(key), json.dumps(result))

            return result

    def write(self, key: str, values: list[T]) -> list[str]:
        object_ids = self._mongo.insert(self._collection, values)
        self._redis.write(self._cache_key(key), json.dumps(values))
        return [str(id) for id in object_ids]

    def write_one(self, key: str, value: T) -> str:
        object_id = self._mongo.insert_one(self._collection, value)
        self._redis.write(self._cache_key(key), json.dumps(value))
        return str(object_id)

    def upsert(self, key: str, value: T, query: MongoQuery) -> str:
        upsert_id = self._mongo.upsert(
            self._collection, query['filter'], value)
        return str(upsert_id)
