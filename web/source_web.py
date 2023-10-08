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
from utils.utils import deal_json_invaild, str_is_none
from dao.task_dao import *
from service.chat_service import chat_service
from service.task_service import *
from service.candidate_filter import candidate_filter, preprocess, judge_and_update_force
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

@source_web.route("/recruit/account/task/fetch", methods=['POST'])
@web_exception_handler
def task_fetch_api():
    account_id = request.json['accountID']
    logger.info(f'account task fetch request {account_id}')
    task_list = get_undo_task(account_id)

    logger.info(f'account task fetch {account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web.route("/recruit/account/task/report", methods=['POST'])
@web_exception_handler
def task_report_api():
    account_id = request.json['accountID']
    ## job use first register job of account:
    # job_id = json.loads(get_account_jobs_db(account_id))[0]
    job_id = request.json.get('jobID', "")
    logger.info(f'job_test:{job_id}')
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        job_id = json.loads(get_account_jobs_db(account_id))[0]
    job_config = json.loads(get_job_by_id(job_id)[0][6],strict=False)
    job_touch_msg = job_config['touch_msg']

    task_status = request.json['taskStatus']
    logger.info(f'account task report {account_id},{job_id} {task_status}')
    touch_list = []
    for item in task_status:
        if item['taskType']=='batchTouch':
            touch_list+= item['details']['candidateList']
    update_touch_task(account_id, job_id, len(touch_list))
    for candidate_id in touch_list:
        candidate_name, filter_result = query_candidate_name_and_filter_result(candidate_id)
        init_msg = {
            'speaker': 'robot',
            'msg': job_touch_msg,
            'time': format_time(datetime.now())
        }
        details = json.dumps([init_msg], ensure_ascii=False)
        new_chat_db(account_id, job_id, candidate_id, candidate_name, filter_result=filter_result, details=details, source='search')

    ret_data = {
        'status': 'ok'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web.route("/recruit/candidate/filter", methods=['POST'])
@web_exception_handler
def candidate_filter_api():
    account_id = request.json['accountID']
    ## job use first register job of account:
    job_id = request.json.get('jobID', "")
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        job_id = json.loads(get_account_jobs_db(account_id))[0]
    # job_id = json.loads(get_account_jobs_db(account_id))[0]
    raw_candidate_info = request.json['candidateInfo']
    #应该从下面取， 不应该在这取吧？@润和 如果是怕异常得换个地方,我换到实现类里面
    # candidate_id, candidate_name = raw_candidate_info['geekCard']['geekId'], raw_candidate_info['geekCard']['geekName']
    candidate_info = None
    ret_data = {
        'touch': False
    }
    candidate_id, candidate_name = "", ""
    # try:
    candidate_info = preprocess(account_id, raw_candidate_info)
    ##todo encode
    candidate_info['id'] = process_independent_encode(account_id, candidate_info['id'])
    
    candidate_id, candidate_name, age, degree, location, position,active_time = candidate_info['id'], candidate_info['name'], candidate_info['age'],\
                                                                    candidate_info['degree'], candidate_info['exp_location'], candidate_info['exp_position'],candidate_info['active_time']
    logger.info(f'candidate filter request {account_id}, {job_id}, {candidate_id}, {candidate_name}, {age}, {degree}, {location}, {active_time}')

    if not query_candidate_exist(candidate_id):
        candidate_info_json = json.dumps(candidate_info, ensure_ascii=False)
        new_candidate_db(candidate_id, candidate_name, age, degree, location, position, candidate_info_json)
    filter_result = candidate_filter(job_id, candidate_info)
    # filter_result = judge_and_update_force(account_id, filter_result)
    to_touch = filter_result['judge']
    ret_data = {
        'touch': to_touch
    }
    logger.info(f'candidate filter {account_id}, {job_id}, {candidate_info}: {filter_result}')
    # except BaseException as e:
    #     logger.info(f'candidate filter request {account_id} {job_id} {candidate_id}, {candidate_name} failed for {e}, {traceback.format_exc()}')
    #     with open(f'test/fail/{candidate_id}_{candidate_name}.json', 'w') as f:
    #         f.write(json.dumps(raw_candidate_info, indent=2, ensure_ascii=False))
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

    logger.info(f'candidate recall request {account_id}, {len(candidate_ids)}, {len(candidate_ids_read)}')
    res_data = recall_msg(account_id, candidate_ids, candidate_ids_read)
    for item in res_data:
        candidate_id = item['candidate_id']
        job_id = item['job_id']
        msg = item['recall_msg']
        append_chat_msg(account_id, job_id, candidate_id, msg)
    logger.info(f'candidate recall response {account_id}, {len(res_data)}')
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

@source_web.route("/recruit/candidate/chat", methods=['POST'])
@web_exception_handler
def candidate_chat_api():
    account_id = request.json['accountID']
    candidate_id = request.json['candidateID']
    #encode
    candidate_id = process_independent_encode(account_id, candidate_id)

    ## job use first register job of account:
    job_id = request.json.get('jobID', "")
    if job_id is None or job_id == "" or job_id == "NULL" or job_id == "None":
        job_id_info = get_job_id_in_chat(account_id, candidate_id)
        if len(job_id_info) == 0:
            job_id = json.loads(get_account_jobs_db(account_id))[0]
        else:
            job_id = job_id_info[0][0]
    # history_msg = request.json['historyMsg']
    candidate_name = request.json.get('candidateName', None)
    page_history_msg = request.json['historyMsg']
    logger.info(f'candidate chat request: {account_id} {job_id} {candidate_id} {candidate_name} {page_history_msg}')

    source = None
    db_history_msg = None

    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        details = json.dumps(page_history_msg, ensure_ascii=False)
        logger.info(f'candidate chat not in db, new candidate will supply: {account_id} {job_id} {candidate_id} {candidate_name} {details}')
        new_chat_db(account_id, job_id, candidate_id, candidate_name, source, details=details)
    else:
        source, db_history_msg, _ = candidate_info[0]
        # logger.info(f'show candidate: {source} {db_history_msg}: {db_history_msg is not None}')
        if db_history_msg is None or db_history_msg =='None':
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
    logger.info(f'candidate chat: {account_id} {job_id} {candidate_id} {candidate_name}: {ret_data}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@source_web.route("/recruit/candidate/result", methods=['POST'])
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
            job_id = json.loads(get_account_jobs_db(account_id))[0]
        else:
            job_id = job_id_info[0][0]

    name = request.form['candidateName']
    phone = request.form.get('phone', None)
    wechat = request.form.get('wechat', None)

    logger.info(f'candidate result, request form: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}; files: {request.files}, file keys:{request.files.keys()}')

    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        logger.info(f'candidate result: {account_id} {job_id} candidate {candidate_id} {name} not in db, will new chat first')
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
    logger.info(f'candidate result request: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')

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
    send_candidate_info(job_id, name, contact['cv'], contact['wechat'], contact['phone'], db_history_msg)
    logger.info(f'candidate result update: {job_id}, {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))



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
