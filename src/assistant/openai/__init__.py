from .openai_wrapper import OpenAIWrapper

import os

__all__ = [
    'openai'
]

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", '')
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL") or "gpt-3.5-turbo"

if not OPENAI_API_KEY:
    raise ValueError("Missing env var OPENAI_API_KEY.")

openai = OpenAIWrapper(OPENAI_API_KEY, OPENAI_MODEL)
