import hashlib
import random
import string
import time


# Use the system PRNG if possible
try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings
    warnings.warn(
        "A secure pseudo-random number generator is not available "
        "on your system. Falling back to Mersenne Twister."
    )
    using_sysrandom = False


SECRET_KEY = ""
DEFAULT_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_md5(data):
    """获取md5"""
    m = hashlib.md5()
    m.update(data.encode())
    return m.hexdigest()


def get_random_string(length=12, allowed_chars=DEFAULT_CHARS):
    """
    Returns a securely generated random string.
    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            hashlib.sha256(
                ("%s%s%s" % (random.getstate(), time.time(), SECRET_KEY)).encode("utf-8")
            ).digest()
        )
    return "".join(random.choice(allowed_chars) for _ in range(length))


def get_random_num(length=12):
    return get_random_string(length, "0123456789")


def generate_random_str(length):
    """生成随机字符串"""
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def is_all_chinese(keyword):
    """判断纯汉字"""
    for uchar in keyword:
        if "\u4e00" <= uchar <= "\u9fa5":
            pass
        else:
            return False

    return True
