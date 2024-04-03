from ..datastore.redisdb.redisdb import get_redis
from typing import Any

import json
import logging


redis = get_redis()


class AssistantState:
    # ToDo: Change to TypedDict, move save() to AssistantService

    def __init__(self, id: str, state: dict[str, Any]):
        self._id = id
        self._state = state

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    def set(self, key: str, value: Any):
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def save(self):
        state = json.dumps(self.state)
        logging.info(f'Saving state {self._id}: {state}')
        redis.write(self._id, state)

    def toJSON(self):
        return json.dumps(self.state)
