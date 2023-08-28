from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from lk_utils.log.base import error
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        resp = dict({
            "total": self.page.paginator.count,
            "page": self.page.number,
            "page_size": self.page.paginator.per_page,
            "items": data,
        })
        return Response(resp)


def page_handle(queryset, serializer, params, context=None, exclude=None, fields=None):
    page = int(params.get('page', 1))
    page_size = int(params.get('page_size', 1000))
    paginator = Paginator(queryset, page_size)

    kwargs = {}
    page_data = []
    if exclude:
        kwargs.setdefault('exclude', exclude)
    if fields:
        kwargs.setdefault('fields', fields)
    if context:
        kwargs.setdefault('context', context)

    try:
        serializer = serializer(
            paginator.page(page), many=True, **kwargs
        )
    except (EmptyPage, Exception) as err:
        error('djangox', f'page fail: {err}')

    if page <= paginator.num_pages:
        page_data = serializer.data

    return {
        'total': paginator.count,
        'total_page': paginator.num_pages,
        'page': page, 'items': page_data,
    }
