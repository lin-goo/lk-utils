# -*- coding: utf-8 -*-
import os

from lk_utils.geoip.ip2Region import Ip2Region


current_dir = os.path.dirname(os.path.abspath(__file__))
searcher = Ip2Region(os.path.join(current_dir, "ip2region.db"))


def get_ip_info(ip):
    try:
        data = searcher.memorySearch(ip)
        location = data["region"].decode("utf-8").split("|")
        city = location[3].replace("0", "")
        province = location[2].replace("0", "")
    except Exception:  # noqa
        city = ""
        province = ""

    return province, city
