import os
import json
from redis import Redis
from asgiref.local import Local
from functools import wraps
from tools.base import get_project_name


class ConfigFileDoesNotExist(Exception):
    pass


class ConnectionDoesNotExist(Exception):
    pass


class ConnectionManager(object):
    config_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self._connections = Local(False)
        self.config_filename = f'{get_project_name()}-config.json'
        self.config_filepath = os.path.join(self.config_dir, self.config_filename)

    @property
    def config(self):
        if not os.path.exists(self.config_filepath):
            raise ConfigFileDoesNotExist(f"The config file `{self.config_filename}` doesn't exist.")
        with open(self.config_filepath, 'r') as fp:
            data = json.load(fp)
        return data

    def create_connection(self, alias):
        params = self.config[alias]
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
            if alias not in self.config:
                raise ConnectionDoesNotExist(f"The connection '{alias}' doesn't exist.")
        conn = self.create_connection(alias)
        setattr(self._connections, alias, conn)
        return conn

    def __setitem__(self, key, value):
        setattr(self._connections, key, value)

    def __delitem__(self, key):
        delattr(self._connections, key)

    def __iter__(self):
        return iter(self.config)


def connection_client(alias):
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
