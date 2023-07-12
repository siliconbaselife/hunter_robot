import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time
import multiprocessing
import sys

lock = multiprocessing.Lock()
_logger_dict = {}


def safe_remove(dict_obj, delete_fun, args):
    del_ids = []
    for k in dict_obj:
        if delete_fun(k):
            del_ids.append(k)
    for k in del_ids:
        del dict_obj[k]


class SafeRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        TimedRotatingFileHandler.__init__(
            self, filename, when, interval, backupCount, encoding, delay, utc)

    '''
    Override doRollover
    lines commanded by '##' is changed by cc
    '''

    def doRollover(self):
        '''
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.

        Override,   1. if dfn not exist then do rename
                    2. _open with 'a' model
        '''
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.baseFilename + '.' + time.strftime(self.suffix, timeTuple)
        # if os.path.exists(dfn):
        # os.remove(dfn)

        # Issue 18940: A file may not have been created if delay is True.
        # if os.path.exists(self.baseFilename):
        with lock:
            if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
            if self.backupCount > 0:
                for s in self.getFilesToDelete():
                    os.remove(s)

        if not self.delay:
            self.mode = 'a'
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


def init_logger(log_dir='./log', log_name='ana.log', level='info'):
    if level == 'info':
        real_level = logging.INFO
    elif level == 'debug':
        real_level = logging.DEBUG

    ret_logger = logging.getLogger(log_name)
    ret_logger.setLevel(real_level)

    formatter = logging.Formatter(
        '[%(asctime)-15s] [%(levelname)s] %(message)s')

    if log_dir is None:
        hdl = logging.StreamHandler()
        hdl.setFormatter(formatter)
        hdl.setLevel(real_level)
    else:
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        log_file = os.path.join(log_dir, log_name)
        hdl = SafeRotatingFileHandler(
            log_file, when='midnight', encoding='utf-8')

        hdl.setFormatter(formatter)
        hdl.setLevel(real_level)

    ret_logger.addHandler(hdl)
    # ret_logger.addHandler(logging.StreamHandler(sys.stdout))
    return ret_logger


def get_logger(log_name):
    global _logger_dict
    if log_name in _logger_dict:
        return _logger_dict[log_name]
    else:
        cur_logger = init_logger(log_name=log_name)
        _logger_dict[log_name] = cur_logger
        return cur_logger