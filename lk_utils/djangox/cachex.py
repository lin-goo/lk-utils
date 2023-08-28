from collections.abc import Iterable

from django.db.models import Q
from lk_utils.cachex import operations


def get_item(model, filter_dict=None, force_reload=False, cache_name='default'):
    item = operations.get_item(model, filter_dict, force_reload, cache_name)
    if not item:
        filters = [Q(deleted=0)]
        for k, v in filter_dict.items():
            if isinstance(v, Iterable):
                filters.append(Q(**{f'{k}__in': v}))
            else:
                filters.append(Q(k=v))

        item = model.objects.filter(*filters).first()
        cache_key, item = operations.get_item(item)
        operations.set_item(cache_key, item, cache_name)

    return item
