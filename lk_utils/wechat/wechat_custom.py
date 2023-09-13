# -*- coding: utf-8 -*-
import logging
import functools

from lk_utils.register import context
from lk_utils.wechat import wechat_client
from wechatpy.exceptions import WeChatClientException
from requests.exceptions import ConnectionError


celery = context['celery']
logger = logging.getLogger(__name__)


def custom_service_resp():
    def decorator(func):
        @functools.wraps(func)
        def warpper(*args, **kwargs):
            log_patten = (
                "[客服接口] %s推送信息失败，APP_ID: %s"
                " OPENID:%s" % (func.__name__, args[0], args[1]) + "错误代码:%d，错误信息：%s"
            )
            args = (arg for index, arg in enumerate(args) if index != 0)
            try:
                return func(wechat_client, *args, **kwargs)
            except WeChatClientException as e:
                logger.warning(log_patten % (e.errcode, e.errmsg))
            except ConnectionError:
                logger.warning(log_patten % (0, "网络连接出错"))

            return False

        return warpper

    return decorator


@celery.task
@custom_service_resp()
def send_text(client, openid, content):
    """组装文本回复数据"""
    return client.message.send_text(openid, content)


@celery.task
@custom_service_resp()
def send_image(client, openid, media_id):
    """组装图片回复数据"""
    return client.message.send_image(openid, media_id)


@celery.task
@custom_service_resp()
def send_music(client, openid, title, desc, music_url, hqmusicurl, thumb_media_id):
    """组装音乐回复数据"""
    return client.message.send_music(
        openid, music_url, hqmusicurl, thumb_media_id, title=title, description=desc
    )


@celery.task
@custom_service_resp()
def send_news(client, openid, content):
    """组装图文回复数据"""
    return client.message.send_articles(openid, articles=content)


@celery.task
@custom_service_resp()
def send_template_msg(
    client, openid, template_id, content, url="", xcx_app_id=None, page_path=None
):
    """发送模板信息通用接口"""
    mini_program = {"appid": xcx_app_id, "pagepath": page_path}
    return client.message.send_template(
        openid, template_id, content, url=url, mini_program=mini_program
    )


@celery.task
@custom_service_resp()
def send_card_msg(client, openid, card_id, card_ext, account=None):
    """
    发送卡券消息

    详情请参参考
    http://mp.weixin.qq.com/wiki/1/70a29afed17f56d537c833f89be979c9.html

    :param openid: 用户 openid
    :param card_id: 卡券 ID
    :param card_ext: 卡券扩展信息
    :param account: 可选，客服账号
    :param client: 微信接口（无需填写）
    :return: 返回的 JSON 数据包
    """
    return client.message.send_card(openid, card_id, card_ext, account)


@custom_service_resp()
def upload_media(client, media_type, media_file):
    """组装媒体回复数据"""
    media_info = client.media.upload(media_type, media_file)
    return media_info


@celery.task
@custom_service_resp()
def send_mini_program(client, openid, appid, title, pagepath, thumb_media_id):
    """
    :param openid: 发送对象openid
    :param appid: 小程序appid
    :param title: 小程序卡片标题
    :param pagepath: 小程序访问路径
    :param thumb_media_id: 小程序缩略图id
    :param client: 微信接口（无需填写）
    :return:
    """
    miniprogrampage = {
        "title": title,
        "appid": appid,
        "pagepath": pagepath,
        "thumb_media_id": thumb_media_id,
    }
    return client.message.send_mini_program_page(openid, miniprogrampage)
