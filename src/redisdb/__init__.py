from .redisdb import RedisDB

__all__ = ['redis']

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 6379
DEFAULT_DB = 0

redis = RedisDB(host=DEFAULT_HOST, port=DEFAULT_PORT, db=DEFAULT_DB)