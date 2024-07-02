import logging
import os
import sys

from concurrent_log_handler import ConcurrentRotatingFileHandler


# 安装命令
# pip install concurrent_log_handler -i https://pypi.tuna.tsinghua.edu.cn/simple

class Logger:
    __instance = None  # 日志管理器实例
    __logMap = {}  # 日志记录器实例

    _CRITICAL = 50
    _ERROR = 40
    _WARNING = 30
    _INFO = 20
    _DEBUG = 10

    _nameToLevel = {
        'CRITICAL': _CRITICAL,
        'ERROR': _ERROR,
        'WARNING': _WARNING,
        'INFO': _INFO,
        'DEBUG': _DEBUG,
        'critical': _CRITICAL,
        'error': _ERROR,
        'warning': _WARNING,
        'info': _INFO,
        'debug': _DEBUG
    }

    def _find_caller(self):
        """
        获取原始调用者及函数名
        :return:
        """

        def wrapper(*args):
            # 获取调用该函数的文件名、函数名及行号
            filename = sys._getframe(1).f_code.co_filename
            funcname = sys._getframe(1).f_code.co_name
            lineno = sys._getframe(1).f_lineno

            # 将原本的入参转变为列表，再把调用者的信息添加到入参列表中
            args = list(args)
            args.append(f'[{os.path.basename(filename)}] [{funcname}] [line:{lineno}]')
            self(*args)

        return wrapper

    def __init__(self, config):
        self._level = config.get('level')  # 记录日志的等级
        self._filepath = config.get('filepath')  # 日志文件存放位置
        self._prefix_name = config.get('prefix_name')  # 日志文件前缀名
        self._filesize = config.get('filesize')  # 单个日志文件大小,单位MB

    def __new__(cls, config, *args, **kwargs):
        """
        单例模式,保证全局只有一个日志管理器
        :param config:
        :param args:
        :param kwargs:
        """
        if Logger.__instance is None:
            Logger.__instance = object.__new__(cls)
        return Logger.__instance

    def _get_logger(self, level):
        """
        获取一个日志记录器
        :param level: 记录器等级
        :return: 日志记录器
        """
        logger = self.__logMap.get(self._prefix_name + '_' + level)
        if logger is not None:
            return logger
        else:
            try:
                if not os.path.isdir(self._filepath):
                    os.makedirs(self._filepath)
                logger = logging.getLogger(self._prefix_name + '_' + level)
                self.__logMap[self._prefix_name + '_' + level] = logger
                filename = '%s/%s_%s.txt' % (self._filepath, self._prefix_name, level)
                formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
                handler = ConcurrentRotatingFileHandler(filename, "a", self._filesize * 1024 ** 2, 3)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(self._nameToLevel[self._level])
                return logger
            except Exception as e:
                raise Exception('创建日志失败', e)

    @_find_caller
    def debug(self, msg, caller=''):
        logger = self._get_logger('debug')
        logger.debug(f'{caller} - {msg}')

    @_find_caller
    def info(self, msg, caller=''):
        logger = self._get_logger('info')
        logger.info(f'{caller} - {msg}')

    @_find_caller
    def warning(self, msg, caller=''):
        logger = self._get_logger('warning')
        logger.warning(f'{caller} - {msg}')

    @_find_caller
    def error(self, msg, caller=''):
        logger = self._get_logger('error')
        logger.error(f'{caller} - {msg}')

    @_find_caller
    def critical(self, msg, caller=''):
        logger = self._get_logger('critical')
        logger.critical(f'{caller} - {msg}')
