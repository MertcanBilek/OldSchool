import logging, os
try:
    from .consts import *
except ImportError:
    from consts import *

class Logger:
    def __init__(self, name:str):
        self.formatter = logging.Formatter(loggerOpts.format)
        self.path = os.path.join(os.path.dirname(__file__),"..",loggerOpts.directory)
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        self.file = ".".join((str(name),loggerOpts.file))
        self._debug = self._logger(name, logging.DEBUG)
        self._info = self._logger(name, logging.INFO)
        self._warn = self._logger(name, logging.WARN)
        self._error = self._logger(name, logging.ERROR)
        self._fatal = self._logger(name, logging.FATAL)

    def debug(self, msg, *args, exc_info=False):
        self._debug.debug(msg,*args,exc_info=exc_info)

    def info(self, msg, *args, exc_info=False):
        self._debug.info(msg,*args,exc_info=exc_info)
        self._info.info(msg,*args,exc_info=exc_info)

    def warn(self, msg, *args, exc_info=False):
        self._debug.warning(msg,*args,exc_info=exc_info)
        self._info.warning(msg,*args,exc_info=exc_info)
        self._warn.warning(msg,*args,exc_info=exc_info)

    def error(self, msg, *args, exc_info=False):
        self._debug.error(msg,*args,exc_info=exc_info)
        self._info.error(msg,*args,exc_info=exc_info)
        self._warn.error(msg,*args,exc_info=exc_info)
        self._error.error(msg,*args,exc_info=exc_info)

    def fatal(self, msg, *args, exc_info=False):
        self._debug.fatal(msg,*args,exc_info=exc_info)
        self._info.fatal(msg,*args,exc_info=exc_info)
        self._warn.fatal(msg,*args,exc_info=exc_info)
        self._error.fatal(msg,*args,exc_info=exc_info)
        self._fatal.fatal(msg,*args,exc_info=exc_info)

    def _addHandler(self, logger:logging.Logger, level:int) -> None:
        file = ".".join((_levels[level],self.file))
        file = os.path.join(self.path,file)
        fileHandler = logging.FileHandler(file)
        fileHandler.setFormatter(self.formatter)
        logger.addHandler(fileHandler)

    def _logger(self, name, level) -> logging.Logger:
        logger = logging.Logger(name)
        self._addHandler(logger, level)
        return logger

_levels = {0:"notset",10:"debug",20:"info",30:"warn",40:"error",50:"fatal"}

if __name__ == "__main__":
    import time
    l = Logger("test")
    l.warn("HAHAHAH %s",time.asctime())