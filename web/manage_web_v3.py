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

from service.manage_service_v2 import *
from service.manage_service import cookie_check_service
from service.task_service import get_undo_task
from dao.manage_dao import update_hello_ids, get_hello_ids, hello_sent_db

manage_web_v2 = Blueprint('manage_web_v3', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@manage_web_v2.route("/recruit/account/task/fetch/v3", methods=['POST'])
@web_exception_handler
def task_fetch_api():
    account_id = request.json['accountID']
    job_id = request.json.get('jobID', "")
    logger.info(f'account_task_fetch_request_v2, {account_id}, {job_id}')
    task_list = get_undo_task(account_id, job_id, 'v2')

    logger.info(f'account_task_fetch_v2,{account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

## TODO
@manage_web_v2.route("/backend/manage/myAccountList/v3", methods=['POST'])
@web_exception_handler
def my_account_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_ret = my_account_list_service_v2(manage_account_id)
    logger.info(f'account_list_query_result_v2:{manage_account_id}, {account_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(account_ret), ensure_ascii=False))

## TODO
@manage_web_v2.route("/backend/manage/taskUpdate/v3", methods=['POST'])
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
    update_config_service_v2(manage_account_id, account_id, platform, params)

    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))

## TODO
@manage_web_v2.route("/backend/manage/metaConfig/v3", methods=['POST'])
@web_exception_handler
def meta_config():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    a = json.load(open('file/meta_config.json'))
    return Response(json.dumps(get_web_res_suc_with_data(a), ensure_ascii=False))


