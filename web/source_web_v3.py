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
from utils.utils import deal_json_invaild, str_is_none,get_default_job,get_default_job_v2, process_linkedin_id
from dao.task_dao import *
from service.chat_service import chat_service
from service.task_service import *
from service.candidate_filter import candidate_filter, preprocess, judge_and_update_force,preprocess_v2
from service.recall_service import recall_msg, recall_result
from service.db_service import append_chat_msg
import json
import math
import traceback
from datetime import datetime

source_web_v2 = Blueprint('source_web_v3', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@source_web_v2.route("/recruit/candidate/filter/v3", methods=['POST'])
@web_exception_handler
def candidate_filter_api_v2():
    account_id = request.json['accountID']
    ## job use first register job of account:
    job_id = request.json.get('jobID', "")
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        return Response(json.dumps(get_web_res_fail('job_id为空'), ensure_ascii=False))
    
    raw_candidate_info = request.json['candidateInfo']
    candidate_info = None
    ret_data = {
        'touch': False
    }
    platform_type = query_account_type_db(account_id)
    candidate_info = preprocess_v2(account_id, raw_candidate_info, platform_type)
    candidate_id, candidate_name = get_id_name(candidate_info, platform_type)
    if platform_type == 'Linkedin':
        candidate_id = process_linkedin_id(candidate_id)
    candidate_info['id'] = process_independent_encode(account_id, candidate_id)

    if not query_candidate_exist(candidate_id):
        candidate_info_json = json.dumps(candidate_info, ensure_ascii=False)    
        logger.info(f"new_candidate_v2 {candidate_info['id']}, {candidate_name}")
        new_candidate_db(candidate_id, candidate_name, '', '', '', '', candidate_info_json)

    filter_result = candidate_filter(job_id, candidate_info)
    to_touch = filter_result['judge']
    ret_data = {
        'touch': to_touch
    }
    logger.info(f'candidate_filter_v2 {account_id}, {job_id}, {candidate_info}: {filter_result}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web_v2.route("/recruit/candidate/chat/v3", methods=['POST'])
@web_exception_handler
def candidate_chat_api():
    account_id = request.json['accountID']
    candidate_id = request.json['candidateID']
    platform_type = query_account_type_db(account_id)
    if platform_type == 'Linkedin':
        candidate_id = process_linkedin_id(candidate_id)
    #encode
    candidate_id = process_independent_encode(account_id, candidate_id)

    ## job use first register job of account:
    job_id = request.form.get('jobID', None)
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        job_id_info = get_job_id_in_chat(account_id, candidate_id)
        if len(job_id_info) == 0:
            ##默认给一个job
            platform_type = query_account_type_db(account_id)
            job_id = get_default_job_v2(platform_type)
        else:
            job_id = job_id_info[0][0]

    candidate_name = request.json.get('candidateName', None)
    page_history_msg = request.json['historyMsg']
    logger.info(f'candidate_chat_v2 request: {account_id} {job_id} {candidate_id} {candidate_name} {page_history_msg}')

    source = None
    db_history_msg = None

    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        details = json.dumps(page_history_msg, ensure_ascii=False)
        logger.info(f'candidate_chat_v2, candidate chat not in db, new candidate will supply: {account_id} {job_id} {candidate_id} {candidate_name} {details}')
        new_chat_db(account_id, job_id, candidate_id, candidate_name, source, details=details)
    else:
        source, db_history_msg, _ = candidate_info[0]
        # logger.info(f'show candidate: {source} {db_history_msg}: {db_history_msg is not None}')
        if db_history_msg is None or db_history_msg =='None' or db_history_msg == "":
            source=None
            db_history_msg=None
        else:
            try:
                db_history_msg = json.loads(db_history_msg, strict=False)
            except BaseException as e:
                logger.info(f'db msg json parse abnormal, proc instead (e: {e}), (msg: {db_history_msg})')
                db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)

    robot_api = query_robotapi_db(job_id)
    if not robot_api:
        reason = f'job id {job_id} 未注册，没有对应的算法uri'
        return Response(json.dumps(get_web_res_fail(reason)))

    chat_context = chat_service(account_id, job_id, candidate_id, robot_api, \
        page_history_msg, db_history_msg, source)

    ret_data = {
        'nextStep': chat_context['next_step'],
        'nextStepContent': chat_context['next_msg'] 
    }
    details = json.dumps(chat_context['msg_list'], ensure_ascii=False)
    update_chat_db(account_id, job_id, candidate_id, chat_context['source'], chat_context['status'], details)
    logger.info(f'candidate_chat_v2: {account_id} {job_id} {candidate_id} {candidate_name}: {ret_data}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))