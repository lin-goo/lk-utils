import functools


def ip_into_int(ip):
    # 先把 192.168.31.46 用map分割'.'成数组，然后用reduuce+lambda转成10进制的 3232243502
    # (((((192 * 256) + 168) * 256) + 31) * 256) + 46
    return functools.reduce(lambda x, y: (x << 8) + y, map(int, ip.split(".")))


# 方法1：掩码对比
def is_internal_ip(ip_str):
    ip_int = ip_into_int(ip_str)
    net_A = ip_into_int("10.255.255.255") >> 24
    net_B = ip_into_int("172.31.255.255") >> 20
    net_C = ip_into_int("192.168.255.255") >> 16
    net_ISP = ip_into_int("100.127.255.255") >> 22
    net_DHCP = ip_into_int("169.254.255.255") >> 16
    return (
        ip_int >> 24 == net_A
        or ip_int >> 20 == net_B
        or ip_int >> 16 == net_C
        or ip_int >> 22 == net_ISP
        or ip_int >> 16 == net_DHCP
    )
