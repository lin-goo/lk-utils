from lk_utils.register_config import context


def update_or_add_instance(model, instance, kvs, update_fields=None):
    """
    创建或更新对象

    Args:
        model: 模型类
        instance: 模型对象
        kvs: 字段名-字段值
        update_fields: 需要修改的字段列表

    Returns:

    """
    db = context['db']
    if not instance:
        instance = model()
        for key, value in kvs.items():
            if hasattr(instance, key) and (kvs.get(key) is not None):
                setattr(instance, key, value)

        db.session.add(instance)

    for key in update_fields or []:
        if hasattr(instance, key) and (kvs.get(key) is not None):
            setattr(instance, key, kvs[key])

    db.session.commit()
    return instance
