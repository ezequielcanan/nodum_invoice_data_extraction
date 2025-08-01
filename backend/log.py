import logging
from logging.handlers import TimedRotatingFileHandler
import sys

class Log():
    logger: logging.Logger = None
    def __init__(self, logname: str = "my_app.log"):
        self.logname = logname
        try:
            self.logger = self.start_log()
        except:
            print(f"Error inicializando Log '{self.logname}.log'")

    def start_log(self):
        logFormatter = logging.Formatter("%(asctime)s - [%(levelname)-5.5s] -  %(message)s")
        # [%(threadName)-12.12s] - 
        logger = logging.getLogger()

        handler = TimedRotatingFileHandler(f"logs/{self.logname}.log", delay=False, when="midnight", backupCount=30, encoding="utf-8")
        handler.suffix = "%Y-%m-%d"
        handler.setFormatter(logFormatter)
        logger.addHandler(handler)

        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.DEBUG)

        return logger

    def info (self, msg: str):
        self.logger.info(msg)

    def debug (self, msg: str):
        self.logger.debug(msg)

    def error (self, msg: str):
        self.logger.error(msg)