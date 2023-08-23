import re
import time
import hashlib
import datetime


def md5sum(src):
    m = hashlib.md5()
    m.update(src.encode())
    return m.hexdigest()


def cdn_auth_a(uri, key, exp=None):
    """鉴权方式A"""
    if not exp:
        exp = int(time.time()) + 1 * 3600

    p = re.compile("^(http://|https://)?([^/?]+)(/[^?]*)?(\\?.*)?$")
    if not p:
        return None

    m = p.match(uri)
    scheme, host, path, args = m.groups()
    if not scheme:
        scheme = "http://"
    if not path:
        path = "/"
    if not args:
        args = ""

    rand = "0"  # "0" by default, other value is ok
    uid = "0"  # "0" by default, other value is ok
    sstring = "%s-%s-%s-%s-%s" % (path, exp, rand, uid, key)
    hashvalue = md5sum(sstring)
    auth_key = "%s-%s-%s-%s" % (exp, rand, uid, hashvalue)
    if args:
        return "%s%s%s%s&auth_key=%s" % (scheme, host, path, args, auth_key)
    else:
        return "%s%s%s%s?auth_key=%s" % (scheme, host, path, args, auth_key)


def cdn_auth_b(uri, key, exp=None):
    """鉴权方式B"""
    if not exp:
        exp = int(time.time()) + 1 * 3600

    p = re.compile("^(http://|https://)?([^/?]+)(/[^?]*)?(\\?.*)?$")
    if not p:
        return None

    m = p.match(uri)
    scheme, host, path, args = m.groups()
    if not scheme:
        scheme = "http://"
    if not path:
        path = "/"
    if not args:
        args = ""

    # convert unix timestamp to "YYmmDDHHMM" format
    nexp = datetime.datetime.fromtimestamp(exp).strftime("%Y%m%d%H%M")
    sstring = key + nexp + path
    hashvalue = md5sum(sstring)
    return "%s%s/%s/%s%s%s" % (scheme, host, nexp, hashvalue, path, args)
