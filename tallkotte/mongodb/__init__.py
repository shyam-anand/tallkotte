import os

__all__ = [
    'mongo_config'
]


mongo_config = {
    'MONGO_HOST': os.environ.get('MONGO_HOST', 'localhost'),
    'MONGO_USERNAME': os.environ.get('MONGO_USERNAME', 'root'),
    'MONGO_PASSWORD': os.environ.get('MONGO_PASSWORD', 'toor'),
    'MONGO_DATABASE': os.environ.get('MONGO_DATABASE', 'cvassistant'),
}
