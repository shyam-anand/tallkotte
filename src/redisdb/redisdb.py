from typing import Any
from redis import Redis
from typing import Optional

import logging


class RedisDB:
    _connection: Optional[Redis] = None
    _is_connected: bool = False

    def __init__(self, host: str, port: int, db: int):
        self._host = host
        self._port = port
        self._db = db

        self.connect()

    def connect(self):
        logging.info(f'Connecting to Redis [{self._host}:{self._port}]')
        self._connection = Redis(
            self._host, self._port, self._db, decode_responses=True)

        if not self._connection.ping():  # type: ignore
            raise RuntimeError('Redis connection failed')

        self._is_connected = True
        logging.info('Redis connection established')

    @property
    def connection(self) -> Redis:
        if (self._connection is None) or (self._is_connected == False):
            self.connect()

        return self._connection  # type: ignore[return-value]

    def read(self, key: str) -> Any | None:
        c = self.connection
        value = c.get(key)  # type: ignore[no-any-return]

        logging.debug(f'Read: {key} -> {type(value)} {value}')  # type: ignore

        if value is not None and value.startswith('__dict__'):  # type: ignore
            return self.h_read(value)  # type: ignore[no-any-return]

        return value  # type: ignore[return-value]

    def write(self, key: str, value: Any) -> bool:
        if value is None:
            logging.warning('Value is None, ignoring.')

        c = self.connection
        if type(value) is dict:
            dict_key = f'__dict__{key}'
            self.h_set(dict_key, value)  # type: ignore
            set_successful = c.set(key, dict_key)  # type: ignore
        else:
            set_successful = c.set(key, value)  # type: ignore

        if set_successful:
            logging.info('Written: {} -> {}'.format(key, value))  # type: ignore
        else:
            logging.warning(
                'Write failed: {} -> {}'.format(key, value))  # type: ignore

        return set_successful  # type: ignore[return-value]

    def h_read(self, key: str) -> dict[Any, Any] | None:
        logging.info('Reading dict: {}'.format(key))
        dict_value = self.connection.hgetall(key)  # type: ignore[no-any-return]
        logging.info('h_read: {} -> ({}) {}'.format(key,
                     type(dict_value), dict_value))  # type: ignore

    def h_set(self, key: str, value: dict[Any, Any]) -> bool:
        logging.info(
            'Setting dict: {} -> ({}) {}'.format(key, type(value), value))
        hset_response = self.connection.hset(  # type: ignore[no-any-return]
            key, mapping=value)
        logging.info('h_set: {} -> ({}) {}'.format(key,
                     type(hset_response), hset_response))
        return hset_response  # type: ignore[return-value]
