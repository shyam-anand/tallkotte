from dotenv import load_dotenv
from flask import Flask
from pathlib import Path
from typing import Any, Mapping

import os
import logging

_SRC_ROOT = Path(__file__).parent
_APP_ROOT = _SRC_ROOT.parent

dotenv_path = os.path.join(_APP_ROOT, '.env')
if not load_dotenv(dotenv_path=dotenv_path):
    raise RuntimeError(f'Error loading .env file [{dotenv_path}]')

_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

logging.basicConfig(
    level=logging.getLevelName(_LOG_LEVEL),  # if args.debug else logging.INFO,
    format=(
        '%(asctime)s %(threadName)s %(filename)s:%(lineno)d %(levelname)s - '
        '%(message)s'
    )
)


def create_app(test_config: Mapping[str, Any] | Any = None):
    logging.info('Creating Flask app')

    # These imports are here so that load_dotenv() is already invoked.
    from .assistant import get_assistant_id
    from .assistant.openai import openai_config
    from .mongodb import mongo_config
    from .redisdb import redis_config

    flask_config = test_config or {
        'SECRET_KEY': 'dev',
    }

    flask_config.update(openai_config)  # type: ignore
    flask_config.update(mongo_config)  # type: ignore
    flask_config.update(redis_config)  # type: ignore
    flask_config.update({  # type: ignore
        'OPENAI_ASSISTANT_ID': get_assistant_id(_APP_ROOT)
    })

    # create and configure Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(flask_config)

    with app.app_context():
        from . import api
        app.register_blueprint(api.bp)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
