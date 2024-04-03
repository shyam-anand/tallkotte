from .openai_wrapper import OpenAIWrapper
from flask import current_app, g
import os

__all__ = [
    'openai_config'
]

_DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env')


OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL: str = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

openai_config = {
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'OPENAI_MODEL': OPENAI_MODEL,
}


def get_openai() -> OpenAIWrapper:
    if 'openai' not in g:
        g.openai = OpenAIWrapper(
            api_key=current_app.config['OPENAI_API_KEY'],  # type: ignore
            model=current_app.config['OPENAI_MODEL'],  # type: ignore
        )

    return g.openai
