from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.group_msg import send_candidate_info
from utils.utils import format_time,get_api_conifg
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.utils import encrypt, decrypt, generate_random_digits,str_is_none, get_stat_id_dict
from dao.task_dao import *
from service.task_service import generate_task
from service.manage_service import *
from utils.utils import key
import json
import math
import traceback
from datetime import datetime

manage_web = Blueprint('manage_web', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@manage_web.route("/recruit/candidate/list", methods=['GET'])
@web_exception_handler
def candidate_list_web():
    job_id = request.args.get('job_id')
    page_num = request.args.get('page_num')
    limit = request.args.get('limit')
    if job_id == None or page_num == None or limit == None:
        logger.info(f'candidade_list_bad_request: job_id: {job_id}， page_num {page_num}')
        return Response(json.dumps(get_web_res_fail("no args")))

    limit = int(limit)
    page_num = int(page_num)

    logger.info(f'candidade_list: job_id: {job_id}， page_num {page_num}')
    start = limit * (page_num - 1)
    
    chat_sum, res_chat_list = candidate_list_service(job_id, start, limit)
    # logger.info(f"{chat_sum}")
    page_sum = math.ceil(chat_sum / limit)
    res = {
        "chat_sum" : chat_sum,
        "page_sum" : page_sum,
        "chat_list" : res_chat_list
    }
    response = Response(json.dumps(get_web_res_suc_with_data(res), ensure_ascii=False))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response

@manage_web.route("/backend/manage/job/register", methods=['POST'])
@web_exception_handler
def register_job_api():
    platform_type = request.json['platformType']
    # platform_id = request.json['platformID']
    platform_id = str(generate_random_digits(10))
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', "")
    robot_api = request.json.get('robotApi',"")
    job_config = request.json.get('jobConfig', None)
    robot_template = request.json.get('robotTemplate', "")
    custom_filter = int(request.json.get('customFilter', 0))
    # share = request.json['share']
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}, {manage_account_id}, {robot_template}')

    ##给字段设定默认值
    share = 0
    job_config = {}
    job_config['custom_filter'] = custom_filter
    if custom_filter == 0:
        job_config['filter_config'] = config['job_register'][platform_type]["filter_config"]
    else:
        job_config['filter_config'] = config['job_register'][platform_type]["custom_filter_config"]
    job_config['chat_config'] = config['job_register'][platform_type]["chat_config"]
    job_config['recall_config'] = config['job_register'][platform_type]["recall_config"]
    manage_config = json.loads(get_manage_config_service(manage_account_id))
    job_config['group_msg'] = manage_config['group_msg']



    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}, {share}, {manage_account_id},{robot_template}')
    if job_config is not None:
        job_config = json.dumps(job_config, ensure_ascii=False)
    
    job_id = f'job_{platform_type}_{platform_id}'
    register_job_db(job_id, platform_type, platform_id, job_name, jd, robot_api, job_config, share, manage_account_id,robot_template)
    ret_data = {
        'jobID': job_id
    }
    logger.info(f'new job register: {platform_type} {platform_id} {job_name} {robot_api} {job_config}  {job_id}, {share}, {manage_account_id}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data), ensure_ascii=False))


@manage_web.route("/backend/manage/account/register", methods=['POST'])
@web_exception_handler
def register_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    jobs = request.json.get('jobs', [])
    task_config = request.json.get('taskConfig', None)
    desc = request.json.get('desc', None)
    logger.info(f'new account request: {platform_type} {platform_id} {jobs} {desc} {task_config}, {manage_account_id}')
    account_id = f'account_{platform_type}_{platform_id}'

    if task_config is None:
        task_config = generate_task(jobs)
    register_account_db(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), desc, manage_account_id)
    logger.info(f'new account register: {platform_type} {platform_id} {jobs} {desc}: {account_id} {task_config}, {manage_account_id}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@manage_web.route("/backend/manage/login", methods=['POST'])
@web_exception_handler
def manage_account_login_api():
    user_name = request.json['user_name']
    password = request.json['password']
    logger.info(f'manage_account_login: {user_name}, {password}')
    flag, msg = login_check_service(user_name, password)
    encode_user_name = encrypt(user_name, key)
    resp =  Response(json.dumps(get_web_res_suc_with_data(
        {
            "login_ret": flag,
            "errMsg": msg,
            "user_name":encode_user_name
        }
    ), ensure_ascii=False))
    if flag:
        resp.set_cookie('user_name', encode_user_name, max_age=None)
    return resp

@manage_web.route("/backend/manage/myJobList", methods=['POST'])
@web_exception_handler
def my_job_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    job_ret = my_job_list_service(manage_account_id)
    logger.info(f'job_list_query_result:{manage_account_id}, {job_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(job_ret), ensure_ascii=False))

@manage_web.route("/backend/manage/myAccountList", methods=['POST'])
@web_exception_handler
def my_account_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    account_ret = my_account_list_service(manage_account_id)
    logger.info(f'account_list_query_result:{manage_account_id}, {account_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(account_ret), ensure_ascii=False))






@manage_web.route("/backend/manage/statistic", methods=['GET'])
@web_exception_handler
def get_ip():
    manage_id = request.args.get('manage_id')
    if manage_id not in get_stat_id_dict():
        return Response(json.dumps(get_web_res_fail("统计账户错误"), ensure_ascii=False))
    manage_account_list = get_stat_id_dict()[manage_id]
    ret = get_stat_service(manage_account_list)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
