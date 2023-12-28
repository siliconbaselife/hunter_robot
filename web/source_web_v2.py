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
from utils.utils import deal_json_invaild, str_is_none,get_default_job,get_default_job_v2
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

source_web_v2 = Blueprint('source_web_v2', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@source_web_v2.route("/recruit/account/task/report/v2", methods=['POST'])
@web_exception_handler
def task_report_api_v2():
    account_id = request.json['accountID']
    ## job use first register job of account:
    # job_id = json.loads(get_account_jobs_db(account_id))[0]
    job_id = request.json.get('jobID', "")
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        return Response(json.dumps(get_web_res_fail('job_id为空'), ensure_ascii=False))
    job_config = json.loads(get_job_by_id(job_id)[0][6],strict=False)
    job_touch_msg = job_config['dynamic_job_config']['touch_msg']

    task_status = request.json['taskStatus']
    logger.info(f'account task report {account_id},{job_id} {task_status}')
    touch_list = []
    for item in task_status:
        if item['taskType']=='batchTouch':
            touch_list+= item['details']['candidateList']
    update_touch_task(account_id, job_id, len(touch_list))
    for candidate_id in touch_list:
        try:
            candidate_id_p = process_independent_encode(account_id, candidate_id)
            candidate_name, filter_result = query_candidate_name_and_filter_result(candidate_id_p)
            init_msg = {
                'speaker': 'robot',
                'msg': job_touch_msg,
                'time': format_time(datetime.now())
            }
            details = json.dumps([init_msg], ensure_ascii=False)
            new_chat_db(account_id, job_id, candidate_id_p, candidate_name, filter_result=filter_result, details=details, source='search')
        except BaseException as e:
            logger.info(f'report_before_filter:{account_id}, {candidate_id}')
    ret_data = {
        'status': 'ok'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web_v2.route("/recruit/candidate/filter/v2", methods=['POST'])
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

@source_web_v2.route("/recruit/candidate/preFilter/v2", methods=['POST'])
@web_exception_handler
def candidate_pre_filter_api_v2():
    account_id = request.json['accountID']
    ## job use first register job of account:
    job_id = request.json.get('jobID', "")
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        return Response(json.dumps(get_web_res_fail('job_id为空'), ensure_ascii=False))

    candidate_id = request.json.get['candidate_id']
    flag,candidate_info = query_candidate_detail(candidate_id)
    if flag:
        filter_result = candidate_filter(job_id, candidate_info)
        to_touch = filter_result['judge']
        ret_data = {
            'touch': to_touch
        }
        logger.info(f'candidate_filter_v2 {account_id}, {job_id}, {candidate_info}: {filter_result}')
        return Response(json.dumps(get_web_res_suc_with_data(ret_data)))
    else:
        logger.info(f'candidate_preFilter_v2 {account_id}, {job_id}, {candidate_id}')
        return Response(json.dumps(get_web_res_suc_with_data({
            "candidate_in_db":False
        })))


@source_web_v2.route("/recruit/candidate/result/v2", methods=['POST'])
@web_exception_handler
def candidate_result_api():
    account_id = request.form['accountID']
    candidate_id = request.form['candidateID']
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

    name = request.form['candidateName']
    phone = request.form.get('phone', None)
    wechat = request.form.get('wechat', None)

    logger.info(f'candidate_result_v2, request form: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}; files: {request.files}, file keys:{request.files.keys()}')

    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        logger.info(f'candidate_result_v2: {account_id} {job_id} candidate {candidate_id} {name} not in db, will new chat first')
        new_chat_db(account_id, job_id, candidate_id, name, source='user_ask')
    #再查一次
    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    _,_,contact = candidate_info[0]
    if contact is None or contact == 'None':
        contact = {
            'phone': None,
            'wechat': None,
            'cv': None
        }
    else:
        contact = json.loads(contact)
    # logger.info(f'candidate result: db contact: {account_id}, {job_id}, {candidate_id}, {name}, info: {candidate_info}, contact: {contact}')
    # if contact is not None and contact!='None':
    #     info_str = f'candidate result for {account_id} {job_id} {candidate_id} already in db'
    #     logger.info(info_str)
    #     return Response(json.dumps(get_web_res_fail(info_str)))

    cv_addr = None
    if len(request.files.keys())>0:
        filename = request.form.get('filename', None)
        if str_is_none(filename):
            ext_name = 'pdf'
        else:
            ext_name = filename.split('.')[-1]
        cv_filename = f'cv_{account_id}_{job_id}_{candidate_id}_{name}.{ext_name}'
        cv_file = request.files['cv'].read()
        cv_addr = generate_thumbnail(cv_filename, cv_file)
    if phone:
        contact['phone'] = phone
    if wechat:
        contact['wechat'] = wechat
    if cv_addr:
        contact['cv'] = cv_addr
    logger.info(f'candidate_result_v2 request: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')

    update_chat_contact_db(account_id, job_id, candidate_id, json.dumps(contact, ensure_ascii=False))
    update_candidate_contact_db(candidate_id, json.dumps(contact,ensure_ascii=False))
    ret_data = {
        'status': 'ok'
    }
    db_history_msg = candidate_info[0][1]
    if db_history_msg is None or db_history_msg =='None':
        db_history_msg = None
    else:
        try:
            db_history_msg = json.loads(db_history_msg, strict=False)
        except BaseException as e:
            logger.info(f'db msg json parse abnormal, proc instead (e: {e}), (msg: {db_history_msg})')
            db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)
    # send_candidate_info(job_id, name, contact['cv'], contact['wechat'], contact['phone'], db_history_msg)
    logger.info(f'candidate_result_update_v2: {job_id}, {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web_v2.route("/recruit/candidate/chat/v2", methods=['POST'])
@web_exception_handler
def candidate_chat_api():
    account_id = request.json['accountID']
    candidate_id = request.json['candidateID']
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