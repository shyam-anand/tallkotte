from ...datastore.cachedstore import CachedStore
from ...datastore.mongodb.mongo_wrapper import get_mongo, MongoDB
from ...datastore.mongodb.mongo_query import mongo_query
from ..openai.datatypes.message import Message
from flask import current_app
from typing import Any, Literal, Mapping, Optional


def _to_message(message_document: Message) -> Message:
    return Message(
        id=message_document['id'],
        role=message_document['role'],
        created_at=message_document['created_at'],
        run_id=message_document['run_id'],
        thread_id=message_document['thread_id'],
        content=message_document['content']
    )


def _convert_to_message(message_dict: dict[str, Any] | Mapping[str, Any]) -> Message:
    return Message(
        id=message_dict['id'],
        role=message_dict['role'],
        created_at=message_dict['created_at'],
        run_id=message_dict['run_id'],
        thread_id=message_dict['thread_id'],
        content=message_dict['content']
    )


cached_store = CachedStore[Message]('messages', _convert_to_message)
mongodb: MongoDB[Message] = get_mongo()


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
    result = cached_store.read(message_id,
                               mongo_query(filter={'id': message_id}))
    if result:
        if isinstance(result, list):
            return result[0]
        return result


def _as_list(result: list[Message] | Message | None) -> list[Message]:
    if result:
        if isinstance(result, list):
            return result
        return [result]
    return []


def find_by_run_id(run_id: str) -> list[Message]:
    result = cached_store.read(run_id,
                               mongo_query(filter={'run_id': run_id})) or []

    return _as_list(result)


def find_by_run_id_and_role(
        run_id: str, role: Literal['user', 'assistant']) -> list[Message]:
    query = mongo_query(filter={
        '$and': [
            {'run_id': run_id},
            {'role': 'assistant'}
        ]
    })
    results = cached_store.read(f'run:{run_id}:role:{role}', query)
    return _as_list(results)
