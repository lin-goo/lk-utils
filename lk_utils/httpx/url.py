from urllib import parse


def url_add_params(url, **params):
    """在网址中加入新参数"""
    pr = parse.urlparse(url)
    query = dict(parse.parse_qsl(pr.query))
    query.update(params)
    prlist = list(pr)
    prlist[4] = parse.urlencode(query)
    return parse.urlunparse(prlist)


def remove_url_query(url, param_list):
    """删除链接中不需要的参数"""
    urls = parse.urlparse(url)
    qs = parse.parse_qs(urls.query)
    for param in param_list:
        if qs.get(param):
            qs.pop(param)
    url_list = list(urls)
    url_list[4] = parse.urlencode(qs, True)
    return parse.urlunparse(url_list)


def url_encoding(url):
    urls = parse.urlparse(url)
    qs = parse.parse_qs(urls.query)
    url_list = list(urls)
    url_list[4] = parse.urlencode(qs, True)
    return parse.urlunparse(url_list)
