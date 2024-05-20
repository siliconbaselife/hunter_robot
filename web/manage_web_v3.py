from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
import json
import math
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail

from utils.utils import encrypt, decrypt, generate_random_digits,str_is_none, get_stat_id_dict
from utils.utils import key

from service.manage_service_v3 import *
from service.manage_service import cookie_check_service
from service.task_service import get_undo_task
from dao.manage_dao import update_hello_ids, get_hello_ids, hello_sent_db

manage_web_v3 = Blueprint('manage_web_v3', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])


## TODO
@manage_web_v3.route("/backend/manage/taskUpdate/v3", methods=['POST'])
@web_exception_handler
def task_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    account_id = request.json['account_id']
    platform = request.json['platform']
    params = request.json['params']

    logger.info(f'task_update_request_v2:{manage_account_id}, {account_id},{platform}, {params}')
    update_config_service_v3(manage_account_id, account_id, platform, params)

    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))

