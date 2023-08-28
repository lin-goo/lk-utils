from asgiref.local import Local
from lk_utils.exceptions import RegisterConfigException


config = Local(False)
context = Local(False)


class ConfigKeys:
    Redis = 'redis'
    OSS = 'oss'


class BaseRegister:
    redis_key = 'REDIS'
    oss_key = 'OSS_CONFIG'

    def __init__(self, settings, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.context = {}
        self.configure = {}
        self.settings = settings
        self.set_variable()

    def set_variable(self):
        self._redis()
        self._oss()
        setattr(config, 'config', self.configure)

    def _redis(self):
        from lk_utils.tools.parserx import parser_redis_url
        raw_config = getattr(self.settings, self.redis_key)
        redis_config = parser_redis_url(raw_config)
        # 设置一个默认配置
        if 'default' not in redis_config:
            first_key = list(redis_config.keys())[0]
            redis_config['default'] = redis_config[first_key]

        self.configure[ConfigKeys.Redis] = redis_config

    def _oss(self):
        raw_config = getattr(self.settings, self.oss_key)
        require_keys = ['access_key_id', 'access_key_secret', 'endpoint', 'bucket']
        oss_config = {key: raw_config[key] for key in require_keys if raw_config.get(key)}
        lack_keys = set(require_keys) - set(oss_config.keys())
        if lack_keys:
            raise RegisterConfigException(
                f'The required configuration items are missing; '
                f'[{self.oss_key}]: {",".join(lack_keys)}'
            )
        # 默认不同步到OSS
        oss_config['is_sync'] = getattr(self.settings, 'SYNC_OSS', False)
        self.configure[ConfigKeys.OSS] = oss_config


class DjangoRegister(BaseRegister):

    def _redis(self):
        raw_config = {
            key: conf['LOCATION'] for key, conf in
            getattr(self.settings, 'CACHES').items()
        }
        setattr(self.settings, self.redis_key, raw_config)
        super()._redis()


class FlaskRegister(BaseRegister):

    def set_variable(self):
        if hasattr(self.kwargs, 'app'):
            for key, value in self.kwargs['app'].__dict__.items():
                setattr(context, key, value)

        super().set_variable()
