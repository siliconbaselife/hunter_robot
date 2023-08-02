import json
from flask import Flask, request, Response
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.utils import deal_json_invaild
from dao.task_dao import *
from service.task_service import generate_task, get_undo_task, update_touch_task
from service.chat_service import ChatRobot
from service.candidate_filter import candidate_filter, preprocess
from utils.log import get_logger
from utils.oss import generate_thumbnail

logger = get_logger(config['log']['log_file'])
app = Flask("robot_backend")

@app.route("/test")
def test():
    return "Hello, World!"


@app.route("/recruit/job/register", methods=['POST'])
@web_exception_handler
def register_job_api():
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', None)
    robot_api = request.json['robotApi']
    # requirement_config = request.json.get('jobRequirement', None)

    # logger.info(f'new job request: {job_name} {requirement_config} {robot_api}')
    logger.info(f'new job request: {job_name} {robot_api}')
    job_id = register_job_db(job_name, jd, robot_api)
    ret_data = {
        'jobID': job_id
    }
    logger.info(f'new job register: {job_name} {robot_api}: {job_id}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@app.route("/recruit/job/query", methods=['POST'])
def query_job_api():
    job_name = request.json['jobName']
    logger.info(f'query job request: {job_name}')

    job_id = query_job_id_db(job_name)
    logger.info(f'job query: {job_name}: {job_id}')
    ret_data = {
        'jobID': job_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/register", methods=['POST'])
def register_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    jobs = request.json['jobs']
    logger.info(f'new account request: {platform_type}, {platform_id}, {jobs}')

    task_config = generate_task(jobs)
    account_id = register_account_db(platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False))
    logger.info(f'new account register: {platform_type}, {platform_id}, {jobs}: {account_id}')
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
    # task_list = [{
    #         "taskID": 1,
    #         "execTime": "2023-07-28 09:10:00",
    #         "jobID": "xxxx",
    #         "taskType": "batchTouch",
    #         "details": {
    #         "mount": 50
    #         }},{
    #         "taskID": 2,
    #         "execTime": "2023-07-28 11:33:00",
    #         "jobID": "xxxx",
    #         "taskType": "chat",
    #         "details": {
    #             "dstList": [{
    #                 "candidateName": "xxx","candidateID": "xxx","msg": "xxx"}]
    #         }
    #     }
    # ]
    logger.info(f'account task fetch {account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


# @app.route("/recruit/account/task/report", methods=['POST'])
# def task_report_api():
#     ### TODO
#     account_id = request.json['accountID']

#     task_status = request.json['taskStatus']

#     logger.info(f'account task report {account_id}, {task_status}')
#     ret_data = {
#         'status': 'ok'
#     }
#     return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/filter", methods=['POST'])
def candidate_filter_api():
    account_id = request.json['accountID']
    job_id = request.json['jobID']
    raw_candidate_info = request.json['candidateInfo']

    candidate_info = preprocess(account_id, raw_candidate_info)
    candidate_id, candidate_name, age, degree, location = candidate_info['id'], candidate_info['name'], candidate_info['age'], candidate_info['degree'], candidate_info['exp_location']
    logger.info(f'candidate filter request {account_id}, {job_id}, {candidate_id}, {candidate_name}, {age}, {degree}, {location}')
    if not query_candidate_exist(candidate_id):
        candidate_info_json = json.dumps(candidate_info, ensure_ascii=False)
        new_candidate_db(candidate_id, candidate_name, age, degree, location, candidate_info_json)
    filter_result = candidate_filter(job_id, candidate_info)
    to_touch = filter_result['judge']
    ret_data = {
        'touch': to_touch
    }
    if to_touch:
        new_chat_db(account_id, job_id, candidate_id, candidate_name)
        update_touch_task(account_id, job_id)
    logger.info(f'candidate filter {account_id}, {job_id}, {candidate_info}: {filter_result}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/chat", methods=['POST'])
def candidate_chat_api():
    account_id = request.json['accountID']

    job_id = request.json['jobID']

    history_msg = request.json['historyMsg']

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
        source, db_history_msg = candidate_info[0]
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
    logger.info(f'candidate result')
    account_id = request.form['accountID']

    job_id = request.form['jobID']

    candidate_id = request.form['candidateID']
    name = request.form['candidateName']
    phone = request.form.get('phone', None)
    wechat = request.form.get('wechat', None)

    logger.info(f'candidate result, files: {request.files}, {request.files.keys()}')

    cv_filename = f'cv_{account_id}_{job_id}_{candidate_id}_{name}.pdf'
    cv_file = request.files['cv'].read()
    cv_addr = generate_thumbnail(cv_filename, cv_file)
    contact = {
        'phone': phone,
        'wechat': wechat,
        'cv': cv_addr
    }

    logger.info(f'candidate result request: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')
    update_chat_contact_db(account_id, job_id, candidate_id, json.dumps(contact, ensure_ascii=False))
    update_candidate_contact_db(candidate_id, json.dumps(contact,ensure_ascii=False))
    ret_data = {
        'status': 'ok'
    }
    logger.info(f'candidate result update: {account_id}, {job_id}, {candidate_id}, {name}, {phone}, {wechat}, {cv_addr}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

if __name__=="__main__":
    app.run(port=2040,host="0.0.0.0",debug=True)
