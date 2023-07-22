import json
from flask import Flask, request, Response
from logger import get_logger
from config import config
from db_operator import *
from web_helper import get_web_res_suc_with_data, get_web_res_fail
from chat import ChatRobot
from utils import deal_json_invaild

logger = get_logger(config['log_file'])
app = Flask("robot_backend")

@app.route("/test")
def test():
    return "Hello, World!"


@app.route("/recruit/job/register", methods=['POST'])
def register_job():
    # request: 
    # jobName: job名称,
    # loginAccountIds: boss用户id列表,
    # jd: 岗位jd
    # robotApi: robot api
    # response
    # return {"ret":0, "msg":"success", "data": xxx}
    job_name = request.json['jobName']
    jd = request.json.get('jd', None)
    robot_api = request.json['robotApi']

    logger.info(f'new job will register: {job_name}, {jd}, {robot_api}')
    new_job(get_db_conn(), job_name, jd, robot_api)
    return Response(json.dumps(get_web_res_suc_with_data('ok')))


@app.route("/recruit/user/register", methods=['POST'])
def register_user():
    # request: 
    # jobName: job名称,
    # loginAccountId: 待添加的boss用户id,
    # response
    # return {"ret":0, "msg":"success", "data": xxx}
    job_name = request.json['jobName']
    login_id = request.json['loginAccountId']

    logger.info(f'new user will register: {job_name}, {login_id}')
    new_user(get_db_conn(), job_name, login_id)
    return Response(json.dumps(get_web_res_suc_with_data('ok')))


@app.route("/recruit/candidate/report", methods=['POST'])
def report_candidate():
    # request: 
    # loginAccountId: boss用户id,
    # candidateId: 候选人id,
    # greeting: 打招呼的话术
    # response
    # return {"ret":0, "msg":"success", "data": xxx}
    login_id = request.json['loginAccountId']
    candidate_id = request.json['candidateId']
    candidate_name = request.json.get('candidateName', None)
    first_msg = request.json['greeting']

    details  = json.dumps([
        {'speaker': 'robot', 'msg': first_msg}
    ], ensure_ascii=False)
    logger.info(f'new candidate will rec: {login_id}, {candidate_id} {candidate_name}, {first_msg}')
    new_candidate(get_db_conn(), login_id, candidate_id, candidate_name=candidate_name, details=details)
    return Response(json.dumps(get_web_res_suc_with_data('ok')))

@app.route("/recruit/candidate/chat", methods=['POST'])
def chat():
    # request: 
    # loginAccountId: boss用户id,
    # candidateId: 候选人id
    # historyMsg: 历史对话信息（[{'speaker": xxx, "msg": xxx},...]）
    # response
    # return {"ret":0, "msg":"success", "data": xxx} 
    # data: { nextStep, nextStepContent };
    # nextStep: enum {"exchange_contact", "received_contact", "chat", "finished"}

    login_id = request.json['loginAccountId']
    candidate_id = request.json['candidateId']
    candidate_name = request.json.get('candidateName', None)
    page_history_msg = request.json['historyMsg']
    logger.info(f'candidate chat: {login_id} {candidate_id} {candidate_name} {page_history_msg}')

    candidate_info = query_candidate(get_db_conn(), login_id, candidate_id)
    last_status = 'init'
    db_history_msg = None
    if candidate_info is None:
        details = json.dumps(page_history_msg, ensure_ascii=False)
        logger.info(f'new candidate will supply: {login_id}, {candidate_id} {candidate_name} {details}')
        new_candidate(get_db_conn(), login_id, candidate_id, candidate_name=candidate_name, details=details)
    else:
        last_status, db_history_msg = candidate_info
        try:
            db_history_msg = json.loads(db_history_msg, strict=False)
        except BaseException as e:
            logger.info(f'db msg json parse abnormal, proc instead (e: {e})')
            db_history_msg = json.loads(deal_json_invaild(db_history_msg), strict=False)

    robot_api = query_robotapi(get_db_conn(), boss_id=login_id)

    sess_id = f'{login_id}_{candidate_id}'
    robot = ChatRobot(robot_api, sess_id, last_status, page_history_msg, db_history_msg=db_history_msg)

    ret_data = {
        'nextStep': robot.next_step,
        'nextStepContent': robot.next_msg 
    }
    details = json.dumps(robot.msg_list, ensure_ascii=False)
    update_candidate(get_db_conn(), login_id, candidate_id, robot.status, details)
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/status", methods=['POST'])
def candidate_status():
    # request: 
    # loginAccountId: boss用户id,
    # candidateId: 候选人id
    # response
    # return {"ret":0, "msg":"success", "data": xxx} 
    # data: { status };
    # status: enum {'no_record', 'init', 'need_contact', 'normal_chat', ...}

    login_id = request.json['loginAccountId']
    candidate_id = request.json['candidateId']
    logger.info(f'candidate status query: {login_id} {candidate_id}')

    candidate_info = query_candidate(get_db_conn(), login_id, candidate_id)
    status = 'no_record'
    if candidate_info is not None:
        status, _ = candidate_info

    ret_data = {
        'status': status,
    }
    logger.info(f'candidate status query {login_id} {candidate_id} ret: {ret_data}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

if __name__=="__main__":
    app.run(port=2020,host="0.0.0.0",debug=True)
