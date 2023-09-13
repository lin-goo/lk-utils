from collections.abc import Iterable
from lk_utils.redisx import operations


def setattr_params(func):
    def wrap(*args, **kwargs):
        model = kwargs.get('model')
        if model:
            model.table_name = model._meta.db_table
            model.db_name = model.objects.db

        return func(*args, **kwargs)

    return wrap


def query_item(model, filter_dict):
    filters = {'deleted': 0}
    for k, v in filter_dict.items():
        if isinstance(v, Iterable):
            filters[f'{k}__in'] = v
        else:
            filters[k] = v

    return model.objects.filter(**filters).first()


@setattr_params
def get_item(model, filter_dict=None, force_reload=False, cache_name='default'):
    return operations.get_item(model, filter_dict, force_reload, cache_name, query_item)


def query_items(model, miss_ids):
    return model.objects.filter(deleted=0, id__in=miss_ids)


@setattr_params
def get_items_by_ids(model, ids, force_reload=False, cache_name='default'):
    return operations.get_items_by_ids(model, ids, force_reload, cache_name, query_items)


@setattr_params
def delete_item_cache(model, filter_dict=None, cache_name='default'):
    return operations.delete_item_cache(model, filter_dict, cache_name)


