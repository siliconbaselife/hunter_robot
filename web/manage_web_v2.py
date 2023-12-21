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


manage_web_v2 = Blueprint('manage_web_v2', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])


@manage_web_v2.route("/backend/manage/account/register/v2", methods=['POST'])
@web_exception_handler
def register_account_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    # manage_account_id = 'xt.test'

    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    jobs = []
    task_config = []
    ver = 'v2'
    account_name = request.json['account_name']
    logger.info(f'new_account_request_v2: {manage_account_id}, {platform_type} {platform_id} {account_name}')
    account_id = f'account_{platform_type}_{platform_id}'

    delete_account_by_id(account_id)
    register_account_db_v2(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), account_name, manage_account_id, ver)
    logger.info(f'new_account_register_v2: {manage_account_id}, {platform_type}, {platform_id}, {jobs}, {account_name},{account_id}, {task_config}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@manage_web_v2.route("/backend/manage/myAccountList/v2", methods=['POST'])
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


@manage_web_v2.route("/backend/manage/taskUpdate/v2", methods=['POST'])
@web_exception_handler
def task_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json['account_id']
    platform = request.json['platform']
    params = request.json['params']

    logger.info(f'task_update_request_v2:{manage_account_id}, {account_id},{platform}, {params}')
    update_config_service_v2(manage_account_id, account_id, platform, params)

    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))


@manage_web_v2.route("/backend/manage/taskActive/v2", methods=['POST'])
@web_exception_handler
def task_active_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json.get('account_id', '')
    job_id = request.json.get('job_id', '')
    active = request.json.get('active', -1)
    if account_id == '' or job_id == '' or active not in [0, 1]:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    logger.info(f'task_active_update_api:{manage_account_id}, {account_id}, {job_id}, {active}')
    flag = update_task_active(manage_account_id, account_id, job_id, active)
    return Response(json.dumps(get_web_res_suc_with_data(flag), ensure_ascii=False))


@manage_web_v2.route("/backend/manage/deleteTask/v2", methods=['POST'])
@web_exception_handler
def delete_task_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json['account_id']
    job_id = request.json['job_id']
    template_id = request.json['template_id']
    logger.info(f'task_update_request:{manage_account_id}, {account_id}, {job_id}, {template_id}')

    ret = delete_config_v2(manage_account_id, account_id, job_id, template_id)

    return Response(json.dumps(get_web_res_suc_with_data(ret)))



