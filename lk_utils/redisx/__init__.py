from functools import wraps
from asgiref.local import Local

from redis import Redis
from lk_utils.register import config
from lk_utils.register import ConfigKeys
from lk_utils.exceptions.redisx import RedisConnectionDoesNotExist


class ConnectionManager(object):

    def __init__(self):
        self._connections = Local(False)

    @property
    def _config(self):
        return getattr(config, ConfigKeys.Redis, None)

    def create_connection(self, alias):
        params = self._config[alias]
        return Redis(**params)

    def close_connection(self, alias):
        conn = getattr(self._connections, alias, None)
        if conn is not None:
            conn.close()
            delattr(self._connections, alias)

    def __getitem__(self, alias):
        try:
            return getattr(self._connections, alias)
        except AttributeError:
            if alias not in self._config:
                raise RedisConnectionDoesNotExist(
                    f"The connection '{alias}' doesn't exist."
                )

        conn = self.create_connection(alias)
        setattr(self._connections, alias, conn)
        return conn

    def __setitem__(self, key, value):
        setattr(self._connections, key, value)

    def __delitem__(self, key):
        delattr(self._connections, key)

    def __iter__(self):
        return iter(self._config)


def connection_redisx(alias):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            connection_manager = ConnectionManager()
            conn = connection_manager[alias]
            try:
                return func(conn, *args, **kwargs)
            finally:
                connection_manager.close_connection(alias)
        return wrapper
    return decorator


client = ConnectionManager()['default']
