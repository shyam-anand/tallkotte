from ...mongodb.mongo_wrapper import get_mongo
from ...redisdb.redisdb import get_redis
from ..openai.datatypes import Message
from flask import current_app
from typing import Any, Literal, Optional, TypedDict, Union

import json

mongodb = get_mongo()
redis = get_redis()


# ToDo: Use!
class MongoQueryBuilder:
    def __init__(self, **initial_query: Any):
        self.query = initial_query

    def and_(self, **condition: Any) -> 'MongoQueryBuilder':
        self.query.setdefault('$and', []).append(condition)
        return self

    def or_(self, **condition: Any) -> 'MongoQueryBuilder':
        self.query.setdefault('$or', []).append(condition)
        return self

    def build(self) -> dict[str, Any]:
        return self.query


class MongoQuery(TypedDict):
    filter: dict[str, Any]
    projection: Optional[dict[str, Any]]
    sort: Optional[dict[str, Any]]
    limit: Optional[int]


def _mongo_query(filter: dict[str, Any],
                 projection: Optional[dict[str, str]] = None,
                 sort: Optional[dict[str, str]] = None,
                 limit: Optional[int] = None) -> MongoQuery:
    return MongoQuery(filter=filter, projection=projection, sort=sort, limit=limit)


def _redis_read(key: str) -> Optional[list[Message]]:
    result = redis.read(f'messages:{key}')
    if result:
        data_dict: Union[dict[str, Any],
                         list[dict[str, Any]]] = json.loads(result)
        if isinstance(data_dict, list):
            return [Message(**item) for item in data_dict]
        else:
            return [Message(**data_dict)]


def _read_through(key: str, on_miss: MongoQuery) -> Optional[list[Message]]:
    cached_result = _redis_read(key)
    if cached_result:
        return cached_result

    db_result = find(**on_miss)
    if db_result:
        result = [_to_message(result) for result in db_result]
        redis.write(f'messages:{key}', json.dumps(result))
        return result


def _to_message(message_document: Message) -> Message:
    return Message(
        id=message_document['id'],
        role=message_document['role'],
        created_at=message_document['created_at'],
        run_id=message_document['run_id'],
        thread_id=message_document['thread_id'],
        content=message_document['content']
    )


def save(messages: list[Message]) -> list[str]:
    try:
        object_ids = mongodb.insert('messages', messages)
        insert_ids = [str(id) for id in object_ids]
        current_app.logger.info(
            f'{len(insert_ids)} messages inserted: {insert_ids}')
        return insert_ids
    except Exception as e:
        current_app.logger.error(f'Error while saving messages: {e}')
        raise RuntimeError('Error while saving messages') from e


def find(filter: Optional[dict[str, Any]] = None,
         projection: Optional[dict[str, Any]] = None,
         sort: Optional[dict[str, Any]] = None,
         limit: Optional[int] = None) -> list[Message]:
    result = mongodb.find('messages', filter, projection, sort, limit)
    return [_to_message(document) for document in result]


def find_by_id(message_id: str) -> Message | None:
    results = _read_through(message_id,
                            _mongo_query(filter={'id': message_id}))
    if results:
        return results[0]


def find_by_run_id(run_id: str) -> list[Message]:
    return _read_through(run_id,
                         _mongo_query(filter={'run_id': run_id})) or []


def find_by_run_id_and_role(
        run_id: str, role: Literal['user', 'assistant']) -> list[Message]:
    query = _mongo_query(filter={
        '$and': [
            {'run_id': run_id},
            {'role': 'assistant'}
        ]
    })
    return _read_through(f'run:{run_id}:role:{role}', query) or []
