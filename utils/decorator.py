# -*- coding: utf-8 -*-

# @Time    : 2020/12/4 上午11:44
# @Author  : gaoqi


import json
import time
import traceback
from functools import wraps

from flask import Response
from utils.log import get_logger

logger = get_logger('./log/server.log')


def web_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        try:
            return func(*args, **kargs)
        except BaseException as e:
            logger.error(traceback.format_exc())
            return Response(json.dumps({'msg': f'exception: {e}', 'status': 0, 'data': []}),
                            mimetype='application/json', status=200)

    return wrapper


def cost_time(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        s = time.time()
        f = func(*args, **kargs)
        print(f"{func.__name__} cost time: {time.time() - s} s")
        logger.info(f"{func.__name__} cost time: {time.time() - s} s")
        return f

    return wrapper


def exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        try:
            return func(*args, **kargs)
        except BaseException as e:
            print(traceback.format_exc())
            logger.error(traceback.format_exc())

    return wrapper


def check_login_handler(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        return func(*args, **kargs)

    return wrapper
