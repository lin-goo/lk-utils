import logging


def write_log(level, name="default"):
    logger = logging.getLogger(name)
    logger.error(level)
    return True


def debug(logger_name, msg, *args):
    log_msg(logger_name, msg, *args, level="debug")


def info(logger_name, msg, *args):
    log_msg(logger_name, msg, *args, level="info")


def warning(logger_name, msg, *args):
    log_msg(logger_name, msg, *args, level="warning")


def error(logger_name, msg, *args):
    log_msg(logger_name, msg, *args, level="error")


def critical(logger_name, msg, *args):
    log_msg(logger_name, msg, *args, level="critical")


def log_msg(logger_name, msg, *args, level="info"):
    """输出信息到日志（可以多个）"""
    if isinstance(logger_name, list):
        names = logger_name
    else:
        names = [logger_name]

    for name in names:
        logger = logging.getLogger(name)
        if logger:
            level = level.lower()
            if level == "debug":
                logger.debug(msg, *args)
            elif level == "info":
                logger.info(msg, *args)
            elif level in ("warn", "warning"):
                logger.warning(msg, *args)
            elif level == "error":
                logger.error(msg, *args, exc_info=True)
            elif level == "critical":
                logger.critical(msg, *args)
