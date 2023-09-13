from lk_utils.register import config
from lk_utils.wechat import wechat_client

from wechatpy import WeChatComponent
from wechatpy.pay import WeChatPay
from wechatpy.session.redisstorage import RedisStorage
from wechatpy.work import WeChatClient


wechat_work = None      # type: WeChatClient
open_platform = None    # type: WeChatComponent
is_debug = True if config.get('DEBUG', True) else False


def init_wechat():
    global open_platform
    open_platform_redis = RedisStorage(
        wechat_client, prefix=config['WECHAT_COMPONENT_PREFIX']
    )
    open_platform_config = config['OPEN_PLATFORM']
    component_config = {
        'component_appid': open_platform_config['APP_ID'],
        'component_appsecret': open_platform_config['APP_SECRET'],
        'component_token': open_platform_config['TOKEN'],
        'encoding_aes_key': open_platform_config['ENCODING_AES_KEY'],
        'session': open_platform_redis,
        'auto_retry': (not is_debug),
    }
    open_platform = WeChatComponent(**component_config)


def init_work_wechat():
    global wechat_work
    wechat_work_redis = RedisStorage(wechat_client, prefix='work_wechat')
    wechat_work = WeChatClient(
        config['WECHAT_WORK']['CorpId'],
        config['WECHAT_WORK']['Secret'],
        session=wechat_work_redis,
        auto_retry=(not is_debug),
    )


def get_client_by_appid(app_id):
    return open_platform.get_client_by_appid(app_id)


def get_pay_client():
    wechat_config = config['WECHAT_CONFIG']
    pay_config = {
        'appid': wechat_config['APP_ID'],
        'api_key': wechat_config['pay_secret'],
        'mch_id': wechat_config['mch_id'],
        'mch_cert': wechat_config['cert_path'],
        'mch_key': wechat_config['key_path'],
    }
    return WeChatPay(**pay_config)


def get_work_wechat_admin_client():
    wechat_config = config['WORK_WECHAT_ADMIN_CONFIG']
    corp_id = wechat_config.get('corp_id')
    secret = wechat_config.get('secret')
    wechat_work_redis = RedisStorage(wechat_client, prefix='work_wechat_admin')
    return WeChatClient(corp_id, secret, session=wechat_work_redis)
