# coding: utf-8
import base64
import hashlib

import requests
from six import BytesIO
from six import string_types

from lk_utils.log.base import error


def send(bot_key, msg_type, **body):
    if (bot_key is None) or (not isinstance(bot_key, string_types)) or (len(body) == 0):
        raise ValueError()

    if not bot_key.startswith("https://"):
        bot_key = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={bot_key}"

    r = requests.post(bot_key, json={"msgtype": msg_type, msg_type: body}, timeout=10)
    if r.status_code != 200:
        error("errors", "[wx_chat_bot] status_code: %s!", r.status_code)
        return False

    response_data = r.json()
    if response_data["errcode"] != 0:
        error("errors", "[wx_chat_bot] errmsg: %s!", response_data["errmsg"])
        return False

    return True


class WeGroupChatBot(object):
    """
    企业微信群机器人接口
    """

    def __init__(self, bot_key):
        """
        初始化群机器人
        :param bot_key: 机器人 Webhook url的key参数或webhook的url
        """
        super(WeGroupChatBot, self).__init__()
        self.bot_key = bot_key

    def send_text(self, content: str, mentioned_list=None, mentioned_mobile_list=None):
        """
        发送纯文本消息，支持相关人提醒功能
        :param content:  发送的文本
        :param mentioned_list:  userid的列表，提醒群中的指定成员(@某个成员)，
                @all表示提醒所有人，如果开发者获取不到userid，可以使用mentioned_mobile_list
        :param mentioned_mobile_list: 手机号列表，提醒手机号对应的群成员(@某个成员)，@all表示提醒所有人
        :return:
        """
        if not mentioned_list:
            mentioned_list = []
        if not mentioned_mobile_list:
            mentioned_mobile_list = []

        return send(
            self.bot_key,
            "text",
            content=content,
            mentioned_list=mentioned_list,
            mentioned_mobile_list=mentioned_mobile_list,
        )

    def send_markdown(self, content):
        """
        发送markdown格式的文本
        :param content: markdown 格式的文本
        :return:
        """
        return send(self.bot_key, "markdown", content=content)

    def send_image(self, filename_or_fp):
        """
        发送图片消息
        :param filename_or_fp: 发送的图片文件路径或句柄,支持JPG、PNG,原图片最大不能超过2M
        :return:
        """
        is_auto_close = False
        if isinstance(filename_or_fp, string_types):
            filename_or_fp = open(filename_or_fp, "rb")
            is_auto_close = True

        buffer = BytesIO()
        buffer.write(filename_or_fp.read())
        byte_data = buffer.getvalue()
        base64_str = repr(base64.b64encode(byte_data))[2:-1]
        md5 = hashlib.md5()
        md5.update(byte_data)
        if is_auto_close:
            filename_or_fp.close()

        return send(self.bot_key, "image", base64=base64_str, md5=md5.hexdigest())

    def send_news(self, news):
        """
        发送一组图文消息
        :param news: 发送图文消息列表
          [
           {
               "title" : "中秋节礼品领取",
               "description" : "今年中秋节公司有豪礼相送",
               "url" : "URL",
               "picurl" : "http://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png"
           }
        ]
        :return:
        """
        if not isinstance(news, (tuple, list)):
            news = [news]
        return send(self.bot_key, "news", articles=news)

    def send_a_news(self, title, url, description=None, picurl=None):
        """
        发送一条图文消息
        :param title: 标题，不超过128个字节，超过会自动截断
        :param url: 点击后跳转的链接。
        :param description: 描述，不超过512个字节，超过会自动截断
        :param picurl: 图文消息的图片链接，支持JPG、PNG格式，较好的效果为大图 1068*455，小图150*150。
        :return:
        """
        return self.send_news(
            {
                "title": title,
                "url": url,
                "description": description,
                "picurl": picurl,
            }
        )
