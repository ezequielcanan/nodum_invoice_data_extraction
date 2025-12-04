import sys, logging
from logging.handlers import TimedRotatingFileHandler
from collections import defaultdict 

class Log():
    logs: dict = dict()
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Log, cls).__new__(cls)
        return cls.instance

    def start_log(cls, logname: str = "my_app.log"):
        logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-5.5s] -  %(message)s")
        # [%(threadName)-12.12s] - 
        logger = logging.getLogger()

        handler = TimedRotatingFileHandler(f"logs/{logname}.log", delay=False, when="midnight", backupCount=30, encoding="utf-8")
        handler.suffix = "%Y-%m-%d"
        handler.setFormatter(logFormatter)
        logger.addHandler(handler)

        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.DEBUG)

        cls.logs[logname] = logger

    def has(cls, logname: str) -> bool:
        if cls.logs.get(logname) is not None:
            return True
        else:
            return False

    def add(cls, logname: str) -> bool:
        cls.start_log(logname)

    def get(cls, logname: str) -> logging.Logger:
        return cls.logs.get(logname)

def log_file(logname: str = "my_app.log") -> bool:
    l = Log()
    if l.has(logname):
        return True
    else:
        try:
            l.add(logname)
            return True
        except:
            return False

def log_info(msg, logname: str = "my_app.log") -> bool:
    l = Log()
    if not l.has(logname):
        if not log_file(logname):
            return False
    log: logging.Logger = l.get(logname)
    if log is not None:
        log.info(msg)
        return True
    else:
        return False

def log_debug(msg, logname: str = "my_app.log") -> bool:
    l = Log()
    if not l.has(logname):
        if not log_file(logname):
            return False
    log: logging.Logger = l.get(logname)
    if log is not None:
        log.debug(msg)
        return True
    else:
        return False

def log_error(msg, logname: str = "my_app.log") -> bool:
    l = Log()
    if not l.has(logname):
        if not log_file(logname):
            return False
    log: logging.Logger = l.get(logname)
    if log is not None:
        log.error(msg)
        return True
    else:
        return False