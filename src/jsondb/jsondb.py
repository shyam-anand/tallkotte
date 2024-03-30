from cvassistant import DATA_DIR
from pathlib import Path
from pathlib import PurePath

import json
import logging
import os


def _filename(key: str) -> Path:
    cwd = Path.cwd()
    return PurePath(os.path.join(DATA_DIR, f'{key}.json'))


def write(data, key: str):
    filename = _filename(key=key)
    logging.info(f'Writing to {filename}')

    with open(filename, 'w') as f:
        json.dump(data, f)


def read(key: str):
    filename = _filename(key=key)
    logging.info(f'Reading from {filename}')

    if Path(filename).is_file():
        if os.stat(filename).st_size == 0:
            return {}
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        logging.info(f'File {filename} does not exist')
