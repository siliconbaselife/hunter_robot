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
    first_msg = request.json['greeting']

    details  = json.dumps([
        {'speaker': 'robot', 'msg': first_msg}
    ], ensure_ascii=False)
    logger.info(f'new candidate will rec: {login_id}, {candidate_id}, {first_msg}')
    new_candidate(get_db_conn(), login_id, candidate_id, details=details)
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
    history_msg = request.json['historyMsg']
    last_status, _ = query_candidate(get_db_conn(), login_id, candidate_id)

    sess_id = f'{login_id}_{candidate_id}'
    robot = ChatRobot(sess_id, history_msg, last_status)

    ret_data = {
        'nextStep': robot.next_step,
        'nextStepContent': robot.next_msg 
    }
    details = json.dumps(robot.msg_list, ensure_ascii=False)
    update_candidate(get_db_conn(), login_id, candidate_id, robot.status, details)
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))



if __name__=="__main__":
    app.run(port=2020,host="0.0.0.0",debug=True)
