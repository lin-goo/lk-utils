#!/usr/bin/python
#
# Copyright (c) 2011 Eran Sandler (eran@sandler.co.il),  http://eran.sandler.co.il,  http://forecastcloudy.net
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
import logging
import socket
import time

from lk_utils.redisx import client


id_worker = None
logger = logging.getLogger("idworker")


class InputError(Exception):
    pass


class InvalidSystemClock(Exception):
    pass


class IdWorker(object):
    def __init__(self, worker_id=0, data_center_id=0):
        self.worker_id = worker_id
        self.data_center_id = data_center_id

        self.logger = logger

        # stats
        self.ids_generated = 6

        # 2018/7/12 10:6:1 GMT + 8
        self.twepoch = 1531361161000

        self.sequence = 0
        self.worker_id_bits = 5
        self.data_center_id_bits = 5
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_data_center_id = -1 ^ (-1 << self.data_center_id_bits)
        self.sequence_bits = 12

        self.worker_id_shift = self.sequence_bits
        self.data_center_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_left_shift = self.sequence_bits + self.worker_id_bits + self.data_center_id_bits
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        self.last_timestamp = -1

        # Sanity check for worker_id
        if self.worker_id > self.max_worker_id or self.worker_id < 0:
            raise InputError("worker_id", "worker id can't be greater than"
                             " %i or less than 0" % self.max_worker_id)

        if self.data_center_id > self.max_data_center_id or self.data_center_id < 0:
            raise InputError("data_center_id", "data center id can't be greater"
                             " than %i or less than 0" % self.max_data_center_id)

        self.logger.info("worker starting. timestamp left shift %d,"
                         " data center id bits %d, worker id bits %d,"
                         " sequence bits %d, worker id %d" % (self.timestamp_left_shift,
                                                              self.data_center_id_bits,
                                                              self.worker_id_bits,
                                                              self.sequence_bits,
                                                              self.worker_id))

    def _time_gen(self):
        return int(time.time() * 1000)

    def _till_next_millis(self, last_timestamp):
        timestamp = self._time_gen()
        while last_timestamp <= timestamp:
            timestamp = self._time_gen()

        return timestamp

    def _next_id(self):
        timestamp = self._time_gen()

        if self.last_timestamp > timestamp:
            self.logger.warning("clock is moving backwards. Rejecting request until %i"
                                % self.last_timestamp)
            raise InvalidSystemClock("Clock moved backwards. "
                                     "Refusing to generate id for %i milliseocnds"
                                     % self.last_timestamp)

        if self.last_timestamp == timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                timestamp = self._till_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        new_id = ((timestamp - self.twepoch) << self.timestamp_left_shift)\
            | (self.data_center_id << self.data_center_id_shift)\
            | (self.worker_id << self.worker_id_shift) | self.sequence
        self.ids_generated += 1
        return new_id

    def get_worker_id(self):
        return self.worker_id

    def get_timestamp(self):
        return self._time_gen()

    def get_id(self):
        new_id = self._next_id()
        self.logger.debug("id: %i worker_id: %i  data_center_id: %i"
                          % (new_id, self.worker_id, self.data_center_id))
        return new_id

    def get_datacenter_id(self):
        return self.data_center_id


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_center_id():
    """分布式机器id"""
    cache_key = 'snowflake_id'
    num_cache_key = 'snowflake_id_num'
    ipaddr = get_host_ip()
    cache_id = int(client.hget(cache_key, ipaddr) or 0)
    if cache_id:
        return cache_id

    # 分配新id
    new_center_id = client.incr(num_cache_key)
    if new_center_id > 31:
        # 超出最大id值,归零
        client.set(num_cache_key, 1)
        new_center_id = 1

    client.hset(cache_key, ipaddr, new_center_id)
    return new_center_id


def init_snowflake(worker_id=0):
    global id_worker
    data_center_id = get_center_id()
    logger.info('[init snowflake] start, data_center_id: %d', data_center_id)
    id_worker = IdWorker(worker_id=0, data_center_id=data_center_id)


def generate_id():
    """
    ID生成接口
    https://segmentfault.com/a/1190000011282426
    """
    return id_worker.get_id()
