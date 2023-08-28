def parser_redis_url(conn_kwargs):
    """
    解析 Redis URL 的连接格式, 转为字典格式

    Args:
        conn_kwargs: {conn_name: conn_url}

    Returns: {conn_name: {**kwargs}}

    """

    config = {}
    for name, url in conn_kwargs.items():
        url, db = url.rsplit('/', 1)
        url, port = url.rsplit(':', 1)
        url, host = url.rsplit('@', 1)
        _, password = url.rsplit(':', 1)
        config[name] = {
            'db': int(db),
            'port': int(port),
            'host': str(host),
            'password': str(password)
        }

    return config
