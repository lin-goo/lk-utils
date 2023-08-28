# -*- coding: utf-8 -*-
import base64
import json
import os

import oss2
from lk_utils.filex.base import gen_filename
from lk_utils.filex.base import get_ext
from lk_utils.log.base import error
from lk_utils.ossx import AUTH
from lk_utils.ossx import OSS_CONFIG
from lk_utils.ossx import SYNC_OSS


BUCKET_DICT = {}


def get_bucket(bucket_name):
    if bucket_name in BUCKET_DICT:
        return BUCKET_DICT[bucket_name]

    bucket = oss2.Bucket(AUTH, OSS_CONFIG['endpoint'], bucket_name)
    BUCKET_DICT[bucket_name] = bucket
    return bucket


def _upload_to_oss(file, file_path, bucket_name):
    if not SYNC_OSS:
        return 200

    try:
        bucket = get_bucket(bucket_name)
        result = bucket.put_object(file_path, file)
    except Exception as e:
        error('errors', f'upload_to_oss process error: {e}')
        return -1

    return result.status


def upload_stream(bucket_name, file_bytes, ext, file_dir, filename=None):
    """
    上传图片数据流
    :param bucket_name: 存储桶名称
    :param file_bytes: 文件流数据
    :param ext: 图片后缀, 例: .png
    :param file_dir: 图片存储目录
    :param filename: 上传到OSS的文件名
    :return:
    """
    if filename is None:
        filename = gen_filename(ext)

    file_path = os.path.join(file_dir, filename).replace('\\', '/')
    status = _upload_to_oss(file_bytes, file_path, bucket_name)
    if status != 200:
        error('errors', f'upload file fail: {status=}')
        return None

    return file_path


def save_img_style(bucket_name, source_image_path, ext, img_dir, style):
    """持久化阿里云处理过的图片"""

    # 生成存储路径
    filename = gen_filename(ext)
    bucket = get_bucket(bucket_name)
    target_image_path = os.path.join(img_dir, filename).replace('\\', '/')
    target_bucket_name = bucket.bucket_name
    process = '{0}|sys/saveas,o_{1},b_{2}'.format(
        style,
        oss2.compat.to_string(base64.urlsafe_b64encode(
            oss2.compat.to_bytes(target_image_path))
        ),
        oss2.compat.to_string(base64.urlsafe_b64encode(
            oss2.compat.to_bytes(target_bucket_name))
        )
    )
    try:
        result = bucket.process_object(source_image_path, process)
    except Exception as e:
        error('errors', f'process_object process error: {e}')
        return None

    if result.status != 200:
        error('errors', f'save_img_style process error: {result.status}')
        return None

    return target_image_path


def copy_oss_file(source_oss_path, save_dir, source_bucket_name, target_bucket_name):
    """拷贝oss"""
    bucket = get_bucket(source_bucket_name)
    ext = get_ext(source_oss_path)
    filename = gen_filename(ext)
    file_path = os.path.join(save_dir, filename).replace('\\', '/')
    result = bucket.copy_object(target_bucket_name, source_oss_path, file_path)
    if result.status != 200:
        error('errors', f'copy_oss_file error: {result.status}')
        return None

    return file_path


def get_oss_filesize(bucket_name, file_path):
    bucket = get_bucket(bucket_name)
    file_obj = bucket.get_object_meta(file_path)
    filesize = file_obj.content_length
    return filesize


def get_oss_file(bucket_name, file_path, process=None, failed_retry=False):
    """
    获取oss文件
    :param bucket_name: bucket
    :param file_path: oss相对路径
    :param process: 处理参数
    :param failed_retry: 失败重试
    :return:
    """
    bucket = get_bucket(bucket_name)
    try:
        result = bucket.get_object(file_path, process=process)
    except Exception as e:
        if failed_retry is False:
            raise e
        error('errors', f'get_oss_file process error: {e}')
        result = bucket.get_object(file_path)

    return result.read()


def get_img_info(bucket_name, file_path):
    """获取图片信息"""
    bucket = get_bucket(bucket_name)
    result = bucket.get_object(file_path, process='image/info')
    return json.loads(result.resp.response.content)


def del_oss_file(bucket_name, file_path):
    bucket = get_bucket(bucket_name)
    try:
        result = bucket.delete_object(file_path)
    except Exception as e:
        error('errors', f'del_oss_file process error: {e}')
        return False

    return bool(result.status == 204)


def is_object_exists(bucket_name, file_path):
    """判断oss文件是否存在"""
    bucket = get_bucket(bucket_name)
    return bucket.object_exists(file_path)


def upload_from_data_url(data_content, dir_name, bucket_name=OSS_CONFIG['bucket']):
    """
    base64 图片流数据上传到OSS
    :param data_content: data:image/jpg;base64,{base64_data}
    :param dir_name: 上传到OSS的文件夹名称
    :param bucket_name: 存储桶名称
    :return:
    """
    ext = '.' + data_content.split(';')[0].split('/')[1]
    b64data = data_content.split(',')[1]
    img_bytes = base64.b64decode(b64data)
    return upload_stream(bucket_name, img_bytes, ext, dir_name)
