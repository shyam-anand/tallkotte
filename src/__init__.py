# package cvassistant
from pathlib import Path

import logging

SRC_ROOT = Path(__file__).parent
APP_ROOT = SRC_ROOT.parent
DATA_DIR = APP_ROOT / 'data'
ASSISTANT_ID_FILENAME = DATA_DIR / 'assistant.json'


logging.basicConfig(
    level=logging.INFO, # if args.debug else logging.INFO,
    format='%(asctime)s %(threadName)s %(filename)s:%(lineno)d %(levelname)s - %(message)s'
)
