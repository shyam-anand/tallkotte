__all__ = [
    'mongodb'
]

from .mongo_wrapper import MongoDB
from typing import Any
import os


def env(name: str, default: Any = None) -> str:
    return os.environ.get(name) or default


MONGO_HOST = env('MONGO_HOST', 'localhost')
MONGO_USERNAME = env('MONGO_USERNAME', 'root')
MONGO_PASSWORD = env('MONGO_PASSWORD', 'toor')
MONGO_DATABASE = env('MONGO_DATABASE', 'cvassistant')


mongodb = MongoDB(
    MONGO_HOST, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
)
