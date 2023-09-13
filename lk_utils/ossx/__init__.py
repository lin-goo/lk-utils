import oss2
from lk_utils.register import config
from lk_utils.register import ConfigKeys


OSS_CONFIG = config[ConfigKeys.OSS]
SYNC_OSS = OSS_CONFIG['is_sync']
AUTH = oss2.Auth(
    OSS_CONFIG['access_key_id'],
    OSS_CONFIG['access_key_secret']
)
