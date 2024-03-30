__all__ = [
    'mongodb'
]

from .mongo_wrapper import MongoDB
from typing import Any
import os


DEFAULT_MONGO_HOST = 'localhost'
DEFAULT_MONGO_USERNAME = 'root'
DEFAULT_MONGO_PASSWORD = 'toor'
DEFAULT_MONGO_DATABASE = 'cvassistant'


def env(name: str, default: Any = None) -> str:
    return os.environ.get(name) or default


mongodb = MongoDB(
    env('MONGO_HOST', DEFAULT_MONGO_HOST),
    env('MONGO_USERNAME', DEFAULT_MONGO_USERNAME),
    env('MONGO_PASSWORD', DEFAULT_MONGO_PASSWORD),
    env('MONGO_DATABASE', DEFAULT_MONGO_DATABASE)
)
