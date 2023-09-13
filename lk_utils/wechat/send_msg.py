# -*- coding: utf-8 -*-
import json
import time
import hashlib
import inspect

import requests
from requests.exceptions import RequestException

from lk_utils.register import config
from lk_utils.log.base import error, warning
from lk_utils.wechat import wechat_client


def get_key_value_str(params):
    """将键值对转为 key1=value1&key2=value2"""
    key_az = sorted(params.keys())
    pair_array = []
    for k in key_az:
        v = str(params.get(k, "")).strip()
        # 微信对无值参数是跳过的，只对有值的处理
        if not v:
            continue
        pair_array.append("%s=%s" % (k, v))

    return "&".join(pair_array)


def md5(unicode_s, is_bin=False):
    """返回MD5特征值"""
    m = hashlib.md5()
    m.update(unicode_s.encode("utf8"))
    if is_bin:
        return m.digest()

    return m.hexdigest()


def get_sign(params, secret):
    """获取签名"""
    if not isinstance(params, dict):
        raise TypeError("%s is not instance of dict" % params)

    params_str = get_key_value_str(params)
    params_str = "%s&key=%s" % (params_str, secret)

    sign = md5(params_str).upper()
    print(params_str, "sign=", sign)
    return sign


def get_access_token(lk_app_id, app_id, force_reload=False, token_type="access_token"):
    cache_key = None
    if token_type == "access_token":
        cache_key = f"{config['WECHAT_COMPONENT_PREFIX']}:{app_id}_access_token"
    elif token_type == "raw_access_token":
        cache_key = f"wechat.get_access_token?ym_app_id={lk_app_id}"

    access_token = wechat_client.get(cache_key)
    if access_token and force_reload is False:
        if isinstance(access_token, bytes):
            access_token = json.loads(access_token.decode("utf8"))
            return access_token

    url = f"{config['AUTH_API_HOST']}/api/wechat/component/token"
    request_data = {
        "timestamp": int(time.time()),
        "api_key": config["AUTH_API_DICT"]["api_key"],
        "lk_app_id": lk_app_id,
        "force_reload": int(force_reload),
        "token_type": token_type,
    }
    sign = get_sign(request_data, config["AUTH_API_DICT"]["api_secret"])
    request_data["sign"] = sign
    try:
        r = requests.get(url, params=request_data, timeout=10)
        r.raise_for_status()
        result = r.json()
        if result["code"] != 200:
            raise Exception(result["msg"])

        access_token = result["data"]["access_token"]
        # cache remote access token
        token_ttl = int(result["data"]["ttl"])
        if access_token and token_ttl > 0:
            # 跟wechatpy库统一
            wechat_client.set(cache_key, json.dumps(access_token), token_ttl)
            return access_token

    except Exception as e:
        error("errors", f"wechat.get_access_token error:{e} request_data:{request_data}")

    return None


def _send_msg(lk_app_id, app_id, url, data, token_type, retry=3):
    """
    发送消息
    :param lk_app_id: lk_app.id
    :param app_id: lk_app.app_id
    :param url: 发送URL
    :param data: 消息内容
    :param retry: 重试次数
    :param token_type: cache prefix
    """

    pre_function_name = inspect.currentframe().f_back.f_code.co_name
    ref = f"[wechat.{pre_function_name}]"
    access_token = get_access_token(lk_app_id, app_id, token_type=token_type)
    if not access_token:
        error("errors", f"{ref} get access_token failed!")
        return False

    is_success = False
    try:
        r = requests.post(f"{url}?access_token={access_token}", json=data, timeout=10)
        r.raise_for_status()
        result = r.json()
    except RequestException as e:
        warning("errors", f"{ref} requests error:%s", e)
    except Exception as e:
        error("errors", f"{ref} error:%s", e)
    else:
        errcode = result.get("errcode")
        if errcode == 0:
            is_success = True
        elif errcode == 40001:  # 无效的access_token
            if retry > 0:
                get_access_token(
                    lk_app_id, app_id, token_type=token_type, force_reload=True
                )
                return _send_msg(
                    lk_app_id, app_id, url, data, token_type, retry=retry - 1
                )
            error("errors", f"{ref} result: %s", result)
        elif errcode != 43101:  # 除了用户拒收订阅信息
            error("errors", f"{ref} result error:%s", result)

    return is_success


def send_subscribe_msg(lk_app_id, app_id, data, retry=3):
    """发送订阅信息"""
    url = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
    return _send_msg(lk_app_id, app_id, url, data, "raw_access_token", retry)


def send_template_msg(lk_app_id, app_id, data, retry=3):
    """发送模板信息"""
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send"
    return _send_msg(lk_app_id, app_id, url, data, "access_token", retry)
