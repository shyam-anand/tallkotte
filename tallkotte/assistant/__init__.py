from pathlib import Path

import json
import logging

__all__ = [
    'get_assistant_id'
]

_ASSISTANT_ID_FILENAME = 'assistant.json'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_assistant_id(assistant_data_path: Path) -> str:
    assistant_id_filepath: Path = assistant_data_path / _ASSISTANT_ID_FILENAME

    logging.info(f'Opening assistant id file: {assistant_id_filepath}')
    if assistant_id_filepath.is_file():
        assistant_id_json = json.loads(assistant_id_filepath.read_text())
        assistant_id = assistant_id_json['id']
        logger.info(f'Found assistant id: {assistant_id}')
        return assistant_id
    else:
        raise ValueError(f'File not found: {assistant_id_filepath}')
