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
from utils.utils import deal_json_invaild, str_is_none,get_default_job,default_job_map
from dao.task_dao import *
from service.chat_service import chat_service
from service.task_service import *
from service.recall_service import recall_msg, recall_result
from service.db_service import append_chat_msg
import json
import math
import traceback
from datetime import datetime


source_web = Blueprint('source_web', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@source_web.route("/recruit/job/query", methods=['POST'])
@web_exception_handler
def query_job_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    logger.info(f'query job request: {platform_type} {platform_id}')

    job_id = query_job_id_db(platform_type, platform_id)
    logger.info(f'job query: {platform_type} {platform_id}: {job_id}')
    ret_data = {
        'jobID': job_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web.route("/recruit/account/query", methods=['POST'])
@web_exception_handler
def query_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']

    logger.info(f'query account request: {platform_type}, {platform_id}')

    account_id = query_account_id_db(platform_type, platform_id)
    logger.info(f'query account: {platform_type}, {platform_id}: {account_id}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@source_web.route("/recruit/candidate/recallList", methods=['POST'])
@web_exception_handler
def candidate_recall_api():
    account_id = request.json['accountID']
    # job_id = json.loads(get_account_jobs_db(account_id))[0]
    candidate_ids = request.json['candidateIDs']
    candidate_ids_read = request.json.get('candidateIDs_read', [])
    
    ## encode
    candidate_ids = process_independent_encode_multi(account_id, candidate_ids)
    candidate_ids_read = process_independent_encode_multi(account_id, candidate_ids_read)

    logger.info(f'candidate recall request {account_id}, {len(candidate_ids)}, {len(candidate_ids_read)}, {candidate_ids}, {candidate_ids_read}')
    res_data = recall_msg(account_id, candidate_ids, candidate_ids_read)
    for item in res_data:
        candidate_id = item['candidate_id']
        job_id = item['job_id']
        msg = item['recall_msg']
        append_chat_msg(account_id, job_id, candidate_id, msg)
    logger.info(f'candidate recall response {account_id}, {len(res_data)}, {res_data}')
    return Response(json.dumps(get_web_res_suc_with_data(res_data), ensure_ascii=False))

@source_web.route("/recruit/candidate/recallResult", methods=['POST'])
@web_exception_handler
def candidate_recall_result_api():
    account_id = request.json['accountID']
    candidate_id = request.json['candidateID']
    
    #encode
    candidate_id = process_independent_encode(account_id, candidate_id)

    logger.info(f'candidate recall request {account_id}, {candidate_id}')
    res_data = recall_result(account_id, candidate_id)
    logger.info(f'candidate recall response {account_id}, {res_data}')
    return Response(json.dumps(get_web_res_suc_with_data(res_data), ensure_ascii=False))

@source_web.route("/recruit/candidate/friendReport", methods=['POST'])
@web_exception_handler
def candidate_friend_report_api():
    account_id = request.json['accountID']
    candidate_id = request.json['candidateID']
    #encode
    candidate_id = process_independent_encode(account_id, candidate_id)

    logger.info(f'friend_report_request {account_id}, {candidate_id}')
    friend_report_service(account_id, candidate_id)
    return Response(json.dumps(get_web_res_suc_with_data(), ensure_ascii=False))


@source_web.route("/recruit/candidate/newOneTimeTask", methods=['POST'])
@web_exception_handler
def new_one_time_task():
    account_id = request.json['accountID']
    one_time_task_config = request.json['one_time_task_config']
    ret = new_one_time_task_service(account_id, one_time_task_config)
    logger.info(f'new_one_time_task: {account_id}, {ret}')
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@source_web.route("/recruit/candidate/oneTimeTaskList", methods=['POST'])
@web_exception_handler
def get_one_time_task_list():
    account_id = request.json['accountID']
    ret = get_one_time_task_list_service(account_id)
    logger.info(f'one_time_task_list: {account_id}, {ret}')
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))


@source_web.route("/recruit/candidate/getOneTimeTask", methods=['POST'])
@web_exception_handler
def get_one_time_task():
    account_id = request.json['accountID']
    ret = get_one_time_task_service(account_id)
    logger.info(f'get_one_time_task: {account_id}, {ret}')
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))


@source_web.route("/recruit/candidate/oneTimeTaskReport", methods=['POST'])
@web_exception_handler
def update_one_time_task():
    task_id = request.json['task_id'] 
    status = request.json['status'] 
    ret = update_one_time_status_service(status, task_id)
    logger.info(f'update_one_time_task_report: {task_id}, {status}')
    return Response(json.dumps(get_web_res_suc_with_data(ret)))


@source_web.route("/recruit/candidate/statistic", methods=['POST'])
@web_exception_handler
def candidate_statistic():  
    return Response(json.dumps(get_web_res_suc_with_data("test")))
