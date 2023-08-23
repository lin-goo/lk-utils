import os
import time
import logging
from hashlib import md5
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter

from tools.base import get_random_string


TWO_MIN = 120
FIVE_MIN = 300
logger = logging.getLogger("network")


def md5_file(file):
    """获取文件md5"""
    m = md5()
    a_file = open(file, "rb")
    m.update(a_file.read())
    a_file.close()
    return m.hexdigest()


def get_dir(file_path):
    return os.path.dirname(file_path)


def get_ext(filename):
    """获取文件名小写后缀，如 .jpg"""
    return os.path.splitext(filename)[1].lower()


def get_file_ext(filename):
    """获取文件后缀，如 jpg"""
    ext = get_ext(filename)
    return ext[1:]


def get_filename(file_path, ext=True):
    """获取文件路径"""
    filename = os.path.basename(file_path)
    if not ext:
        filename = os.path.splitext(filename)[0]
    return filename


def format_filesize(nbytes):
    suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    if nbytes == 0:
        return "0 B"

    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1

    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def get_today_dir():
    """获取当天的文件存储目录，如：2016/11/01"""
    now = datetime.now()
    return "%s/%02d/%02d" % (now.year, now.month, now.day)


def gen_filename(file_ext):
    name = "%s%s" % (get_random_string(30), file_ext)
    filename = os.path.join(get_today_dir(), name)
    return filename


def mkdir_if_not_exists(dest_file_path):
    """判断目标路径的目录是否存在，不存在则创建目录"""
    dest_dir = os.path.dirname(dest_file_path)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)


def get_file_size(photo_file):
    """获取文件大小"""
    # set pos to file end
    photo_file.seek(0, 2)
    filesize = photo_file.tell()
    photo_file.seek(0, 0)
    return filesize


class FileMaxSizeException(requests.exceptions.RequestException):
    pass


def file_download(
    url: str,
    connect_time=3,
    download_timeout=100,
    max_download_size_mb=50,
    is_show_progress=False,
) -> bytes:
    start = time.time()
    file_bytes = b""
    with requests.Session() as s:
        s.mount("http://", HTTPAdapter(max_retries=1))
        s.mount("https://", HTTPAdapter(max_retries=1))
        headers_resp = s.head(url, timeout=connect_time)
        content_length = int(headers_resp.headers.get("Content-Length", 0) or 0)
        if content_length / 1024 / 1024 > max_download_size_mb:
            raise FileMaxSizeException("文件大小超过最大限制")

        resp = s.get(url, stream=True, timeout=connect_time)
        resp.raise_for_status()
        total_chunk_size = 0
        chunk_size = 1024 * 8
        for chunk in resp.iter_content(chunk_size=chunk_size):
            total_chunk_size += chunk_size
            end = time.time()
            if (end - start) > download_timeout:
                raise requests.exceptions.ReadTimeout(
                    "download timeout: %.2fs" % download_timeout, response=resp
                )
            if chunk:
                file_bytes += chunk
            if is_show_progress:
                print("file progress: %.2fmb" % (total_chunk_size / 1024 / 1024))
            if total_chunk_size > max_download_size_mb * 1024 * 1024:
                raise FileMaxSizeException("文件大小超过最大限制", response=resp)

    return file_bytes
