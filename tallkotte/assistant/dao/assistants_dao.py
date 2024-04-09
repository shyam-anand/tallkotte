from ...datastore.cachedstore import CachedStore
from ...datastore.mongodb.mongo_query import MongoQuery, MongoQueryBuilder
from ..openai.datatypes.assistant import Assistant, to_assistant
from openai.types.beta.assistant import Assistant as OpenAiAssistant
from typing import Optional

import logging

cached_store = CachedStore[Assistant]('assistants', to_assistant)


def _has_id(id: str) -> MongoQuery:
    return MongoQueryBuilder(id=id).build()


def save(assistant: Assistant | OpenAiAssistant) -> Assistant:
    if isinstance(assistant, OpenAiAssistant):
        assistant = to_assistant(assistant)

    logging.info(f'save: {assistant['id']} -> {assistant}')
    cached_store.upsert(assistant['id'], assistant, _has_id(assistant['id']))
    return assistant


def get(assistant_id: str) -> Optional[Assistant]:
    result = cached_store.read(assistant_id, _has_id(assistant_id))
    if result:
        return result[0] if isinstance(result, list) else result
