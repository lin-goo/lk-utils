from redis.exceptions import LockError
from redis.lock import Lock as LockBase


class Lock(LockBase):
    """
    使用redis自带Lock改进的锁, 支持阻塞操作, 向下兼容
    默认redis Lock使用Context为阻塞，修改为非阻塞
    """

    def __init__(self, name, *args, **kwargs):
        """
        timeout=None, sleep=0.1, blocking=True,
        blocking_timeout=None, thread_local=True

        :param name: 锁名称
        :param timeout: 锁的存在时间（秒）
        :param blocking: 锁阻塞, 默认关闭
        :param args:
        :param kwargs:
        """
        # 默认20秒超时
        kwargs.setdefault("timeout", 20)
        # 非阻塞
        kwargs.setdefault("blocking", False)
        from lk_utils.redisx import client
        super().__init__(client, name, *args, **kwargs)

    def __enter__(self):
        # force blocking, as otherwise the user would have to check whether
        # the lock was actually acquired or not.
        # 默认blocking为Ture, 向下兼容使用初始化时候的blocking设置
        if self.acquire():
            return self
        # raise LockError("Unable to acquire lock within the time specified")
        return False

    def __exit__(self, exc_type, exc_value, traceback):
        # 退出尝试移除锁，如果已被阻塞直接返回
        try:
            self.release()
        except LockError:
            # Cannot release an unlocked lock
            return False
