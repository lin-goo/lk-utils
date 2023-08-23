#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
from calendar import monthrange
from datetime import date
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta

DATE_PATTERN = "%Y-%m-%d"
DATETIME_PATTERN = "%Y-%m-%d %H:%M:%S"
MONTH_PATTERN = "%Y-%m"
DATETIME_CHINESE_PATTERN = "%Y年%m月%d日 %H:%M"
DATETIME_SHORT_PATTERN = "%y-%m-%d %H:%M"
TIME_PATTERN = "%H:%M"


def simple_format_datetime(dt):
    return dt.strftime(DATETIME_PATTERN)


def simple_format_date(dt):
    return dt.strftime(DATE_PATTERN)


def simple_format_month(dt):
    return dt.strftime(MONTH_PATTERN)


def simple_format_timestamp(dt):
    return int(time.mktime(dt.timetuple()))


def simple_format_time(dt):
    return dt.strftime(TIME_PATTERN)


def simple_format_chinese_datetime(dt):
    return dt.strftime(DATETIME_CHINESE_PATTERN)


def simple_format_short_datetime(dt):
    return dt.strftime(DATETIME_SHORT_PATTERN)


def parse_datetime_str(datetime_str):
    return datetime.strptime(datetime_str, DATETIME_PATTERN)


def parse_date_str(date_str):
    return datetime.strptime(date_str, DATE_PATTERN)


def get_last_day_of_month(year, month):
    """获取指定年月的天数"""
    return monthrange(year, month)[1]


def get_timestamp(dt=None):
    """由 datetime 对象获取对应的时间戳，如: 1460368253

    当 dt 为 None 时获取当前时间的时间戳

    :param dt: datetime 对象
    """
    if not dt:
        return get_current_timestamp
    else:
        if not isinstance(dt, datetime):
            raise TypeError("%s is not a datetime instance." % dt)

    t = time.mktime(dt.timetuple())
    return int(t)


def datetime_str_to_timestamp(datetime_str):
    return get_timestamp(parse_datetime_str(datetime_str))


def datetime_to_timestamp(datetime_obj):
    timestamp = int(
        time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0
    )
    return timestamp


def date_str_to_timestamp(date_str):
    return get_timestamp(parse_date_str(date_str))


def get_current_timestamp():
    """获取当前时间的时间戳"""
    return int(time.time())


def get_tm_delta_seconds(tm_delta):
    if not isinstance(tm_delta, timedelta):
        raise Exception("wrong tm_delta type.")
    return int(tm_delta.total_seconds())


def get_min_datetime_of_the_day(dt):
    """
    获取当天的最小datetime对象
    :param dt: datetime对象
    :return: datetime对象
    """
    if not isinstance(dt, datetime):
        raise Exception("wrong datetime type. %s" % type(dt))
    dt_date = dt.date()
    min_time = dt_time.min  # time(0, 0, 0, 0)
    return datetime.combine(dt_date, min_time)


def get_max_dt_of_the_day(dt):
    dt_date = dt.date()
    max_time = dt_time.max  # time(23, 59, 59, 999999)
    return datetime.combine(dt_date, max_time)


def ts_after_days(days=1):
    """获取几天后的时间戳"""
    date_ = date.today() + timedelta(days=days)
    date_ts = int(time.mktime(date_.timetuple()))
    return date_ts


def sec_to_days_later(days=1):
    """现在到几天后的时间间隔"""
    date_ts = ts_after_days(days=days)
    now_ts = int(time.time())
    return date_ts - now_ts
