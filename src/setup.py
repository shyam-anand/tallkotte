from . import ASSISTANT_ID_FILENAME
from .redisdb import redis
from pathlib import Path

import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def _load_assistant_id(
        assistant_id_filepath: Path = ASSISTANT_ID_FILENAME) -> str:
    def _load_assistant_id() -> str:
        if assistant_id_filepath.is_file():
            assistant_id_json = json.loads(assistant_id_filepath.read_text())
            assistant_id = assistant_id_json['id']
            logger.info(f"Found assistant id: {assistant_id}")
            redis.write('assistant_id', assistant_id)
            return assistant_id
        else:
            raise ValueError(f"File not found: {assistant_id_filepath}")

    return redis.read('assistant_id') or _load_assistant_id()


ASSISTANT_ID = _load_assistant_id()
