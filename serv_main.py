import json
from flask import Flask, request, Response
from logger import get_logger
from config import config
from db_operator import get_db_conn, new_candidate, update_candidate, query_candidate
from web_helper import get_web_res_suc_with_data, get_web_res_fail
from chat import ChatRobot

logger = get_logger(config['log_file'])
app = Flask("robot_backend")

@app.route("/test")
def test():
    return "Hello, World!"

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
        db_history_msg = json.loads(db_history_msg)

    sess_id = f'{login_id}_{candidate_id}'
    robot = ChatRobot(sess_id, page_history_msg, last_status, db_history_msg=db_history_msg)

    ret_data = {
        'nextStep': robot.next_step,
        'nextStepContent': robot.next_msg 
    }
    details = json.dumps(robot.msg_list, ensure_ascii=False)
    update_candidate(get_db_conn(), login_id, candidate_id, robot.status, details)
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))



if __name__=="__main__":
    app.run(port=2020,host="0.0.0.0",debug=True)
