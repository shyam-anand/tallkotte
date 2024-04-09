from flask import Flask
from pathlib import Path
from typing import Any, Mapping

import os
import logging

_SRC_ROOT = Path(__file__).parent
_APP_ROOT = _SRC_ROOT.parent
_UPLOAD_FOLDER = _APP_ROOT / 'uploads'

_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

logging.basicConfig(
    level=logging.getLevelName(_LOG_LEVEL),  # if args.debug else logging.INFO,
    format=(
        '%(asctime)s %(threadName)s %(filename)s:%(lineno)d %(levelname)s - '
        '%(message)s'
    )
)


def _init_upload_folder() -> str:
    if not os.path.exists(_UPLOAD_FOLDER):
        os.mkdir(_UPLOAD_FOLDER)

    return _UPLOAD_FOLDER.as_posix()


def _create_flask_config() -> Mapping[str, Any]:
    # Imports for app configuration
    from .assistant import get_assistant_id
    from .assistant.openai import openai_config
    from .datastore.mongodb import mongo_config
    from .datastore.redisdb import redis_config

    assistant_id = get_assistant_id(_APP_ROOT)  # type: ignore

    flask_config = {
        'SECRET_KEY': 'dev',
        'ASSISTANT_ID': assistant_id,
        'UPLOAD_FOLDER': _init_upload_folder(),
    }

    flask_config.update(openai_config)  # type: ignore
    flask_config.update(mongo_config)  # type: ignore
    flask_config.update(redis_config)  # type: ignore

    return flask_config


def create_app():
    logging.info('---< Creating Flask app >---')

    # create and configure Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(_create_flask_config())

    with app.app_context():
        from . import api
        app.register_blueprint(api.bp)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
