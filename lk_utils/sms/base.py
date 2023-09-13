import json
from lk_utils.register import config
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


client = AcsClient(
    config['SMS_CONFIG']['access_key_id'],
    config['SMS_CONFIG']['access_secret'],
    config['SMS_CONFIG']['region_id'],
)


def send_sms_msg(phone, text):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('dysmsapi.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('https')  # https | http
    request.set_version('2017-05-25')
    request.set_action_name('SendSms')

    request.add_query_param('PhoneNumbers', phone)
    request.add_query_param('SignName', config.SMS_CONFIG['sign_name'])
    request.add_query_param('TemplateCode', config.SMS_CONFIG['template_code'])
    request.add_query_param('TemplateParam', json.dumps({'code': text}))

    response = client.do_action_with_exception(request)
    print(f'send sms: {phone=} {text=} {response=}')
