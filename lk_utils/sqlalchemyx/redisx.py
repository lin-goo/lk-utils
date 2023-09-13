from collections.abc import Iterable
from lk_utils.redisx import operations


def setattr_params(func):
    def wrap(*args, **kwargs):
        model = kwargs.get('model')
        if model:
            model.table_name = model.__tablename__
            model.db_name = getattr(model, '__bind_key__', 'default')

        return func(*args, **kwargs)

    return wrap


def query_item(model, filter_dict):
    filters = [model.deleted == 0]
    for k, v in filter_dict.items():
        if isinstance(v, Iterable):
            filters.append(getattr(model, k).in_(v))
        else:
            filters.append(getattr(model, k) == v)

    return model.query.filter(*filters).first()


@setattr_params
def get_item(model, filter_dict=None, force_reload=False, cache_name='default'):
    return operations.get_item(model, filter_dict, force_reload, cache_name, query_item)


def query_items(model, miss_ids):
    return model.query.filter(model.deleted == 0, model.id.in_(miss_ids))


@setattr_params
def get_items_by_ids(model, ids, force_reload=False, cache_name='default'):
    return operations.get_items_by_ids(model, ids, force_reload, cache_name, query_items)


@setattr_params
def delete_item_cache(model, filter_dict=None, cache_name='default'):
    return operations.delete_item_cache(model, filter_dict, cache_name)


