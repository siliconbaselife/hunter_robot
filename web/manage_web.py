from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.oss import generate_thumbnail
from utils.group_msg import send_candidate_info
from utils.utils import format_time
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.utils import deal_json_invaild
from dao.task_dao import *
from service.task_service import generate_task
from service.manage_service import *

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

@manage_web.route("/recruit/job/register", methods=['POST'])
@web_exception_handler
def register_job_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', None)
    robot_api = request.json.get('robotApi',None)
    job_config = request.json.get('jobConfig', None)
    share = request.json['share']
    manage_account_id = request.json['manage_account_id']
    if job_config is not None:
        job_config = json.dumps(job_config, ensure_ascii=False)

    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}, {share}, {manage_account_id}')
    job_id = f'job_{platform_type}_{platform_id}'
    register_job_db(job_id, platform_type, platform_id, job_name, jd, robot_api, job_config, share, manage_account_id)
    ret_data = {
        'jobID': job_id
    }
    logger.info(f'new job register: {platform_type} {platform_id} {job_name} {robot_api} {job_config}  {job_id}, {share}, {manage_account_id}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@manage_web.route("/recruit/account/register", methods=['POST'])
@web_exception_handler
def register_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    manage_account_id = request.json['manage_account_id']
    jobs = request.json.get('jobs', [])
    task_config = request.json.get('taskConfig', None)
    desc = request.json.get('desc', None)
    logger.info(f'new account request: {platform_type} {platform_id} {jobs} {desc} {task_config}, {manage_account_id}')
    account_id = f'account_{platform_type}_{platform_id}'

    if task_config is None:
        task_config = generate_task(jobs)
    account_id = register_account_db(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), desc, manage_account_id)
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
    return Response(json.dumps(get_web_res_suc_with_data(
        {
            "login_ret": flag,
            "errMsg": msg
        }
    ), ensure_ascii=False))

@manage_web.route("/backend/manage/jobMapping", methods=['POST'])
@web_exception_handler
def job_mapping():
    manage_account_id = request.json['manage_account_id']
    account_id = request.json['account_id']
    job_id = request.json['job_id']
    logger.info(f'job_mapping: {manage_account_id}, {account_id}, {job_id}')
    ret = job_mapping_service(account_id, job_id)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/myJobList", methods=['POST'])
@web_exception_handler
def my_job_list_api():
    manage_account_id = request.json['manage_account_id']
    job_ret = my_job_list_service(manage_account_id)
    logger.info(f'job_list_query_result:{manage_account_id}, {job_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(job_ret), ensure_ascii=False))

@manage_web.route("/backend/manage/myAccountList", methods=['POST'])
@web_exception_handler
def my_account_list_api():
    manage_account_id = request.json['manage_account_id']
    account_ret = my_account_list_service(manage_account_id)
    logger.info(f'account_list_query_result:{manage_account_id}, {account_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(account_ret), ensure_ascii=False))

@manage_web.route("/backend/manage/accountUpdate", methods=['POST'])
@web_exception_handler
def account_update_api():
    manage_account_id = request.json['manage_account_id']
    account_id = request.json['account_id']
    task_config = request.json['task_config']
    logger.info(f'account_update_request:{manage_account_id}, {account_id}, {task_config}')
    ret = account_config_update_service(manage_account_id, account_id, task_config)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))
@manage_web.route("/backend/manage/jobUpdate", methods=['POST'])
@web_exception_handler
def job_update_api():
    return
