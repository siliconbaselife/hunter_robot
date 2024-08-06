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
from service.manage_service_v2 import update_config_service_v2
from service.manage_service import cookie_check_service
from service.task_service import get_undo_task

manage_web_v3 = Blueprint('manage_web_v3', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])


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

    logger.info(f'task_update_request_v3:{manage_account_id}, {account_id},{platform}, {params}')
    if platform == 'Boss':
        update_config_service_v3(manage_account_id, account_id, platform, params)
    else:
        update_config_service_v2(manage_account_id, account_id, platform, params)
        
    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))

@manage_web_v3.route("/backend/manage/metaConfig/v3", methods=['POST'])
@web_exception_handler
def meta_config_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    a = json.load(open('file/meta_config_v3.json'))

    return Response(json.dumps(get_web_res_suc_with_data(a), ensure_ascii=False))


@manage_web_v3.route("/backend/manage/chatStat/v3", methods=['POST'])
@web_exception_handler
def chat_stat_api():
    job_id = request.json.get('jobID', "")
    platform = request.json.get('platform', None)
    begin_time = request.json.get('beginTime', "")
    end_time = request.json.get('endTime', "")
    if platform != 'Boss':
        return Response(json.dumps(get_web_res_fail("非boss平台不支持"), ensure_ascii=False))
    stat_result = stat_chat_service(job_id, begin_time, end_time)
    return Response(json.dumps(get_web_res_suc_with_data(stat_result), ensure_ascii=False))


@manage_web_v3.route("/backend/manage/candidateList/v3", methods=['POST'])
@web_exception_handler
def candidate_list_api():
    job_id = request.json.get('jobID', "")
    platform = request.json.get('platform', None)
    begin_time = request.json.get('beginTime', "")
    end_time = request.json.get('endTime', "")
    if platform != 'Boss':
        return Response(json.dumps(get_web_res_fail("非boss平台不支持"), ensure_ascii=False))
    candidate_list = chat_list_service(job_id, begin_time, end_time)
    return Response(json.dumps(get_web_res_suc_with_data(candidate_list), ensure_ascii=False))
