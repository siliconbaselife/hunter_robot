import json
import math
from flask import Flask, request, Response
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.utils import deal_json_invaild
from dao.task_dao import *
from service.task_service import generate_task, get_undo_task, update_touch_task
from service.chat_service import ChatRobot
from service.manage_service import candidate_list_service
from service.candidate_filter import candidate_filter, preprocess
from utils.log import get_logger
from utils.oss import generate_thumbnail
from utils.group_msg import send_candidate_info
import traceback

from flask_cors import *


logger = get_logger(config['log']['log_file'])
app = Flask("robot_backend")

CORS(app, supports_credentials=True)
CORS(app, resources=r'/*')

@app.route("/test")
def test():
    return "Hello, World!"


@app.route("/recruit/job/register", methods=['POST'])
@web_exception_handler
def register_job_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', None)
    robot_api = request.json['robotApi']
    job_config = request.json.get('jobConfig', None)
    if job_config is not None:
        job_config = json.dumps(job_config, ensure_ascii=False)

    # logger.info(f'new job request: {job_name} {requirement_config} {robot_api}')
    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}')
    job_id = f'job_{platform_type}_{platform_id}'
    register_job_db(job_id, platform_type, platform_id, job_name, jd, robot_api, job_config)
    ret_data = {
        'jobID': job_id
    }
    logger.info(f'new job register: {platform_type} {platform_id} {job_name} {robot_api} {job_config}: {job_id}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@app.route("/recruit/job/query", methods=['POST'])
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


@app.route("/recruit/account/register", methods=['POST'])
def register_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    jobs = request.json['jobs']
    task_config = request.json.get('taskConfig', None)
    desc = request.json.get('desc', None)
    logger.info(f'new account request: {platform_type} {platform_id} {jobs} {desc} {task_config}')
    account_id = f'account_{platform_type}_{platform_id}'

    if task_config is None:
        task_config = generate_task(jobs)
    account_id = register_account_db(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), desc)
    logger.info(f'new account register: {platform_type} {platform_id} {jobs} {desc}: {account_id} {task_config}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/query", methods=['POST'])
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

@app.route("/recruit/account/task/fetch", methods=['POST'])
def task_fetch_api():
    account_id = request.json['accountID']
    logger.info(f'account task fetch request {account_id}')
    task_list = get_undo_task(account_id)

    logger.info(f'account task fetch {account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/task/report", methods=['POST'])
def task_report_api():
    ### TODO
    account_id = request.json['accountID']
    ## job use first register job of account:
    job_id = json.loads(get_account_jobs_db(account_id))[0]
    task_status = request.json['taskStatus']
    logger.info(f'account task report {account_id}, {task_status}')
    touch_list = []
    for item in task_status:
        if item['taskType']=='batchTouch':
            touch_list+= item['details']['candidateList']
    update_touch_task(account_id, job_id, len(touch_list))
    for candidate_id in touch_list:
        candidate_name = query_candidate_name(candidate_id)
        new_chat_db(account_id, job_id, candidate_id, candidate_name)

    ret_data = {
        'status': 'ok'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/filter", methods=['POST'])
def candidate_filter_api():
    account_id = request.json['accountID']
    ## job use first register job of account:
    # job_id = request.json['jobID']
    job_id = json.loads(get_account_jobs_db(account_id))[0]
    raw_candidate_info = request.json['candidateInfo']
    candidate_id, candidate_name = raw_candidate_info['geekCard']['geekId'], raw_candidate_info['geekCard']['geekName']
    candidate_info = None
    ret_data = {
            'touch': False
        }
    try:
        candidate_info = preprocess(account_id, raw_candidate_info)

        candidate_id, candidate_name, age, degree, location, position,active_time = candidate_info['id'], candidate_info['name'], candidate_info['age'],\
                                                                        candidate_info['degree'], candidate_info['exp_location'], candidate_info['exp_position'],candidate_info['active_time']
        logger.info(f'candidate filter request {account_id}, {job_id}, {candidate_id}, {candidate_name}, {age}, {degree}, {location}, {active_time}')

        if not query_candidate_exist(candidate_id):
            candidate_info_json = json.dumps(candidate_info, ensure_ascii=False)
            new_candidate_db(candidate_id, candidate_name, age, degree, location, position, candidate_info_json)
        filter_result = candidate_filter(job_id, candidate_info)
        to_touch = filter_result['judge']
        ret_data = {
            'touch': to_touch
        }
    # if to_touch:
    #     new_chat_db(account_id, job_id, candidate_id, candidate_name)
    #     update_touch_task(account_id, job_id)
        logger.info(f'candidate filter {account_id}, {job_id}, {candidate_info}: {filter_result}')
    except BaseException as e:
        logger.info(f'candidate filter request {account_id} {job_id} {candidate_id}, {candidate_name} failed for {e}, {traceback.format_exc()}')
        with open(f'test/fail/{candidate_id}_{candidate_name}.json', 'w') as f:
            f.write(json.dumps(raw_candidate_info, indent=2, ensure_ascii=False))
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/chat", methods=['POST'])
def candidate_chat_api():
    account_id = request.json['accountID']
    ## job use first register job of account:
    # job_id = request.json['jobID']
    job_id = json.loads(get_account_jobs_db(account_id))[0]
    # history_msg = request.json['historyMsg']
    candidate_id = request.json['candidateID']
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
                logger.info(f'db msg json parse abnormal, proc instead (e: {e})')
                db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)

    robot_api = query_robotapi_db(job_id)
    if not robot_api:
        reason = f'job id {job_id} 未注册，没有对应的算法uri'
        return Response(json.dumps(get_web_res_fail(reason)))


    sess_id = f'{account_id}_{job_id}_{candidate_id}'
    robot = ChatRobot(robot_api, sess_id, page_history_msg, db_history_msg=db_history_msg, source=source)

    ret_data = {
        'nextStep': robot.next_step,
        'nextStepContent': robot.next_msg 
    }
    details = json.dumps(robot.msg_list, ensure_ascii=False)
    update_chat_db(account_id, job_id, candidate_id, robot.source, robot.status, details)
    logger.info(f'candidate chat: {account_id} {job_id} {candidate_id} {candidate_name}: {ret_data}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/result", methods=['POST'])
def candidate_result_api():
    
    account_id = request.form['accountID']

    ## job use first register job of account:
    # job_id = request.form['jobID']
    job_id = json.loads(get_account_jobs_db(account_id))[0]

    candidate_id = request.form['candidateID']
    name = request.form['candidateName']
    phone = request.form.get('phone', None)
    wechat = request.form.get('wechat', None)

    logger.info(f'candidate result, request form: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}; files: {request.files}, file keys:{request.files.keys()}')

    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    if len(candidate_info) == 0:
        logger.info(f'candidate result: {account_id} {job_id} candidate {candidate_id} {name} not in db, will new chat first')
        new_chat_db(account_id, job_id, candidate_id, name)
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
        cv_filename = f'cv_{account_id}_{job_id}_{candidate_id}_{name}.pdf'
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
    if db_history_msg is not None:
        try:
            db_history_msg = json.loads(db_history_msg, strict=False)
        except BaseException as e:
            logger.info(f'db msg json parse abnormal, proc instead (e: {e})')
            db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)
    send_candidate_info(job_id, name, contact['cv'], contact['wechat'], contact['phone'], db_history_msg)
    logger.info(f'candidate result update: {job_id}, {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))




@app.route("/recruit/candidate/list", methods=['GET'])
def candidate_list_web():
    job_id = request.args.get('job_id')
    page_num = request.args.get('page_num')
    limit = request.args.get('limit')
    if job_id == None or page_num == None or limit == None:
        logger.info(f'candidade_list_bad_request: job_id: {job_id}， page_num {page_num}')
        return Response(json.dumps(get_web_res_fail("no args")))


    logger.info(f'candidade_list: job_id: {job_id}， page_num {page_num}')
    start = limit * (int(page_num) - 1) + 1
    
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

    


if __name__=="__main__":
    app.run(port=2040,host="0.0.0.0",debug=True)
