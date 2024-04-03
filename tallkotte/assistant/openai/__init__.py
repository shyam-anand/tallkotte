import os

__all__ = [
    'openai_config'
]


OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL: str = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

openai_config = {
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'OPENAI_MODEL': OPENAI_MODEL,
}
