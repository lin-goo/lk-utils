# -*- coding: utf-8 -*-
import pickle as pickle
import urllib

from lk_utils.redisx import ConnectionManager
from lk_utils.tools.base import is_collection_type
from lk_utils.tools.base import is_func_type
from lk_utils.tools.base import is_value_type


cache_time = 300
FORCE_RELOAD = False


def cached(tm, cache_name='default'):
    def middle(func):
        def wrap(*args, **kwargs):
            module = func.__module__.split('.')[1]
            cache_key = f"{module}.{func.__name__}?{','.join([str(r) for r in args])}"
            cache_key += ','.join([str(r[1]) for r in list(kwargs.items())])
            client = ConnectionManager()[cache_name]
            data = client.get(cache_key)
            force_reload = kwargs.pop('force_reload', None)
            if data and not force_reload:
                return pickle.loads(data)

            data = func(*args, **kwargs)
            if data:
                client.set(cache_key, pickle.dumps(data), tm)
            return data

        return wrap

    return middle


def gen_kv_cache_key(key, val):
    """
    为 kv 生成 cache_key
    :param key: 关键字段 str 类型; 形式 key=val
    :param val: 值字段 支持number, str, function; 形式 func({key})
    :return:
    """
    # number, str
    if is_value_type(val):
        return "{}={}".format(key, val)

    # function, lambda, method
    elif is_func_type(val):
        return "func({})".format(key)

    # list, set
    elif is_collection_type(val):
        return "{}={}".format(key, sort_list_to_str(val))

    else:
        print("Warning: [gen_kv_cache_key]未匹配的值类型! %r, %r" % (key, val))
        return "{}={}".format(str(key), str(val))


def gen_item_cache_key(model, filter_dict):
    """
    生成单个对象缓存key
    :param model: 数据库对象
    :param filter_dict: 筛选字典, {'hash_id': 'abc'}
    :return: mk-photo.album.album?id=1
    """
    db_name = model.db_name
    table_name = model.table_name
    module_name = model.__module__.split('.')[1]
    cache_key = '%s.%s.%s' % (db_name, module_name, table_name)
    if filter_dict:
        key_list = sorted(filter_dict.keys())
        cache_str = '&'.join([gen_kv_cache_key(key, filter_dict[key]) for key in key_list])
        cache_key = '%s?%s' % (cache_key, cache_str)

    return cache_key


def get_item(model, filter_dict=None, force_reload=False, cache_name='default', query_func=None):
    """
    获取数据库对象

    Args:
        model: 模型类
        filter_dict: 过滤字典
        force_reload: 是否强制刷新缓存
        cache_name: 数据库名称
        query_func: 未查询到缓存时，调用的DB查询函数

    Returns:

    """
    if filter_dict is None:
        filter_dict = {}
    if not force_reload:
        force_reload = FORCE_RELOAD

    client = ConnectionManager()[cache_name]
    cache_key = gen_item_cache_key(model, filter_dict)
    item = client.get(cache_key)
    if item and not force_reload:
        return pickle.loads(item)

    if not query_func:
        return None

    client.delete(cache_key)
    item = query_func(model, filter_dict)
    if not item:
        return None

    client.set(cache_key, pickle.dumps(item), cache_time)
    return item


def get_items_by_ids(model, ids, force_reload=False, cache_name='default', query_func=None):
    """
    批量获取数据

    Args:
        model: 模型类
        ids: 单个或多个id列表
        force_reload: 是否强制刷新缓存
        cache_name: 使用的缓存配置名称
        query_func: 未查询到缓存时，调用的DB查询函数

    Returns: {id1: obj, id2: obj}

    """
    if not force_reload:
        force_reload = FORCE_RELOAD

    if isinstance(ids, int):
        ids = [ids]

    cache_keys = []
    for pk in ids:
        cache_key = gen_item_cache_key(model, {'id': pk})
        cache_keys.append(cache_key)

    item_dict, miss_ids = {}, []
    client = ConnectionManager()[cache_name]
    if cache_keys:
        # 强制刷新时先删掉旧缓存
        if force_reload:
            item_list = None
            for cache_key in cache_keys:
                client.delete(cache_key)
        else:
            item_list = client.mget(cache_keys)

        for i, pk in enumerate(ids):
            if item_list and item_list[i]:
                item_dict[pk] = pickle.loads(item_list[i])
            else:
                miss_ids.append(pk)

    if all([miss_ids, query_func]):
        queryset = query_func(model, miss_ids)
        for item in queryset:
            item_dict[item.id] = item
            cache_key = gen_item_cache_key(model, {'id': item.id})
            client.set(cache_key, pickle.dumps(item), cache_time)

    return item_dict


def delete_item_cache(model, filter_dict=None, cache_name='default'):
    """
    删除单个对象缓存

    Args:
        model: 模型类
        filter_dict: 过滤字典
        cache_name: 数据库名称

    Returns:

    """
    client = ConnectionManager()[cache_name]
    cache_key = gen_item_cache_key(model, filter_dict)
    result = client.delete(cache_key)
    return result


def get_item_ids(model, p=1, page_size=10, filter_dict=None, value='id', order_func=None,
                 key_str=None, reverse=True, limit_num=None, cache_name='default'):

    if filter_dict is None:
        filter_dict = {}

    client = ConnectionManager()[cache_name]
    cache_key = set_all_item_cache(model, filter_dict, value, order_func, key_str, limit_num=limit_num)
    if reverse:
        item_ids = client.zrevrange(cache_key, (p - 1) * page_size, p * page_size - 1)
    else:
        item_ids = client.zrange(cache_key, (p - 1) * page_size, p * page_size - 1)

    item_ids = [int(item_id) for item_id in item_ids]
    return item_ids


def get_item_ids_by_score(model, min_score=None, max_score=None, filter_dict=None,
                          value='id', order_func=None, key_str=None, cache_name='default'):

    if (min_score is None) and (max_score is None):
        return get_item_ids(model, 1, 0, filter_dict=filter_dict, value=value, order_func=order_func, key_str=key_str)

    client = ConnectionManager()[cache_name]
    cache_key = set_all_item_cache(model, filter_dict, value, order_func, key_str)
    item_ids = client.zrangebyscore(cache_key, min_score, max_score)
    return item_ids


def get_item_ids_with_score(model, p=1, page_size=10, filter_dict=None, value='id', order_func=None,
                            key_str=None, reverse=True, limit_num=None, cache_name='default'):

    if filter_dict is None:
        filter_dict = {}

    client = ConnectionManager()[cache_name]
    cache_key = set_all_item_cache(model, filter_dict, value, order_func, key_str, limit_num=limit_num)
    if reverse:
        items = client.zrevrange(cache_key, (p - 1) * page_size, p * page_size - 1, withscores=True)
    else:
        items = client.zrange(cache_key, (p - 1) * page_size, p * page_size - 1, withscores=True)

    item_ids = [(int(item_id), int(score)) for item_id, score in items]
    return item_ids


def get_item_amount(model, filter_dict=None, value='id', order_func=None, cache_name='default'):
    client = ConnectionManager()[cache_name]
    cache_key = set_all_item_cache(model, filter_dict, value, order_func)
    amount = client.zcard(cache_key)
    return amount


def set_all_item_cache(model, filter_dict=None, value='id', order_func=None, key_str=None,
                       force_reload=False, limit_num=None, cache_name='default'):
    """
    设置id列表缓存, 用于获取列表数据

    Args:
        model: 模型类
        filter_dict: 过滤字典
        value: 返回属性
        order_func: 排序函数
        key_str: 标识 Key 的字段名称
        force_reload: 是否强制刷新
        limit_num: 限制最大数量
        cache_name: 数据库名称

    Returns: 缓存key

    """

    if filter_dict is None:
        filter_dict = {}
    if not force_reload:
        force_reload = FORCE_RELOAD

    tm = 60 * 30
    client = ConnectionManager()[cache_name]
    cache_key = gen_all_item_cache_key(model, filter_dict, value, key_str)
    if not client.exists(cache_key) or force_reload:
        if order_func:
            items = model.query
        else:
            items = db.session.query(model.id, getattr(model, value))

        items = items.filter(model.deleted == 0)
        for k, v in filter_dict.items():
            if is_func_type(v):
                items = items.filter(v())
            elif is_collection_type(v):
                items = items.filter(getattr(model, k).in_(v))
            else:
                m_field = getattr(model, k)
                items = items.filter(m_field == v)

        if limit_num:
            items = items.order_by(model.id.desc()).limit(limit_num)

        item_tuple = {}
        for item in items:
            if order_func:
                order_value = order_func(item)
            else:
                order_value = item.id  # 默认id排序
            item_tuple.update({getattr(item, value): order_value})

        client.delete(cache_key)
        if item_tuple:
            client.zadd(cache_key, mapping=item_tuple)
            client.expire(cache_key, tm)

    return cache_key


def gen_all_item_cache_key(model, filter_dict=None, value='id', key_str=None):
    """
    生成id列表缓存key

    Args:
        model: 模型类
        filter_dict: 过滤字典
        value: 返回属性
        key_str:

    Returns:

    """
    if filter_dict is None:
        filter_dict = {}

    db_name = model.db_name
    table_name = model.table_name
    module = model.__module__.split('.')[1]
    cache_key = '%s.%s.all_%s_%s' % (db_name, module, table_name, value)
    if key_str:
        cache_key = '%s_%s' % (cache_key, key_str)

    if filter_dict:
        key_list = sorted(filter_dict.keys())
        cache_str = '&'.join([gen_kv_cache_key(key, filter_dict[key]) for key in key_list])
        cache_key = '%s?%s' % (cache_key, cache_str)

    return cache_key


def add_all_item_cache(item, filter_dict=None, value='id', order_func=None, key_str=None, cache_name='default'):
    """
    添加单个id至列表缓存, 用于更新缓存

    Args:
        item:
        filter_dict:
        value: 返回属性
        order_func: 排序函数
        key_str: 设置一个标识key的值
        cache_name:

    Returns:

    """
    if filter_dict is None:
        filter_dict = {}

    client = ConnectionManager()[cache_name]
    cache_key = gen_all_item_cache_key(item, filter_dict, value, key_str)
    if not client.exists(cache_key):
        return True

    if order_func:
        order_value = order_func(item)
    else:
        order_value = item.id  # 默认id排序

    item_tuple = {getattr(item, value): order_value}
    client.zadd(cache_key, mapping=item_tuple)
    return True


def rem_all_item_cache(item, filter_dict=None, value='id', key_str=None, cache_name='default'):
    """
    从id列表缓存中删除单个id, 用于更新缓存

    Args:
        item:
        filter_dict:
        value:
        key_str:
        cache_name:

    Returns:

    """
    if filter_dict is None:
        filter_dict = {}

    client = ConnectionManager()[cache_name]
    cache_key = gen_all_item_cache_key(item, filter_dict, value, key_str)
    if not client.exists(cache_key):
        return True

    client.zrem(cache_key, getattr(item, value))
    return True


def format_number(num):
    """格式化(播放、点赞)数据"""
    if not isinstance(num, int):
        return num

    # 亿级别
    if num >= 100000000:
        return "%.1f亿" % (num / 100000000)

    # 万级别
    elif num >= 10000:
        return "%.1f万" % (num / 10000)

    return str(num)


def fix_pagesize_params(page_size, default, max_num=10):
    """
    矫正 page_size

    Args:
        page_size: 分页参数(待矫正)
        default: 默认分页值, 校验失败时返回的默认值
        max_num: 分页允许最大值, 超过最大分页则校验失败

    Returns:

    """
    if page_size <= 0 or page_size > max_num:
        return default

    return page_size


def urlencodestr(astr):
    if not astr:
        return ""

    if isinstance(astr, bytes):
        astr = astr.decode()

    if len(astr.split(" ")) > 1:
        return urllib.parse.quote_plus(astr)

    return urllib.parse.quote(astr)


def sort_list_to_str(li):
    """
    对列表进行去重、排序后转为字符串
    example: li = [6, 3, 3, 1, 5]
    return:  "1,3,5,6"
    """
    if isinstance(li, (int, str)):
        return str(li)
    elif is_collection_type(li):
        li = sorted(list(set(li)))  # 去重排序
        li = list(map(str, li))  # 转为字符串
        return ",".join(li)
    else:
        raise ValueError("argument list illegal")
