from numbers import Number


def is_value_type(value):
    """
    是否为值类型：Number、str
    """
    return isinstance(value, (Number, str))


def is_func_type(value):
    """
    是否为可调用类型: function、lambda、method...
    """
    return callable(value)


def is_collection_type(value):
    """
    是否为集合类型：list、set
    """
    return isinstance(value, (list, set))


def list_to_dict(lists, key):
    """
    对象列表转为对象字典
    :param lists: 对象列表
    :param key: 对象的某个属性Key
    :return:
    """
    return {getattr(instance, key): instance for instance in lists}
