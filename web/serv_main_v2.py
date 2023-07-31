import json
from flask import Flask, request, Response
from utils.logger import get_logger
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail

logger = get_logger(config['log_file'])
app = Flask("robot_backend")

@app.route("/test")
def test():
    return "Hello, World!"


@app.route("/recruit/job/register", methods=['POST'])
def register_job():
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', None)
    robot_api = request.json['robotApi']

    job_id = 'test_job_id'
    logger.info(f'new job will register: {job_name}, {jd}, {robot_api}: {job_id}')
    ret_data = {
        'jobID': job_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@app.route("/recruit/job/query", methods=['POST'])
def query_job():
    job_name = request.json['jobName']

    job_id = 'test_job_id'
    logger.info(f'job query: {job_name}: {job_id}')
    ret_data = {
        'jobID': job_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/register", methods=['POST'])
def register_account():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']

    accound_id = 'test_accound_id'
    logger.info(f'new account will register: {platform_type}, {platform_id}: {accound_id}')
    ret_data = {
        'accountID': accound_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/query", methods=['POST'])
def query_account():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']

    accound_id = 'test_accound_id'
    logger.info(f'account query: {platform_type}, {platform_id}: {accound_id}')
    ret_data = {
        'accountID': accound_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@app.route("/recruit/account/task/fetch", methods=['POST'])
def task_fetch():
    accound_id = request.json['accountID']

    task_list = [{
            "taskID": 1,
            "execTime": "2023-07-28 09:10:00",
            "jobID": "xxxx",
            "taskType": "batchTouch",
            "details": {
            "mount": 50
            }},{
            "taskID": 2,
            "execTime": "2023-07-28 11:33:00",
            "jobID": "xxxx",
            "taskType": "chat",
            "details": {
                "dstList": [{
                    "candidateName": "xxx","candidateID": "xxx","msg": "xxx"}]
            }
        }
    ]
    logger.info(f'account task fetch {accound_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/account/task/report", methods=['POST'])
def task_report():
    accound_id = request.json['accountID']

    task_status = request.json['taskStatus']

    logger.info(f'account task report {accound_id}, {task_status}')
    ret_data = {
        'status': 'ok'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/filter", methods=['POST'])
def candidate_filter():
    accound_id = request.json['accountID']

    job_id = request.json['jobID']

    candidate_info = request.json['candidateInfo']

    logger.info(f'candidate filter {accound_id}, {job_id}, {candidate_info}')
    ret_data = {
        'touch': True
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@app.route("/recruit/candidate/chat", methods=['POST'])
def candidate_chat():
    accound_id = request.json['accountID']

    job_id = request.json['jobID']

    history_msg = request.json['historyMsg']

    logger.info(f'candidate chat {accound_id}, {job_id}, {history_msg}')
    ret_data = {
        'nextStep': 'need_contact',
        'nextStepContent': '您好'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@app.route("/recruit/candidate/result", methods=['POST'])
def candidate_result():
    accound_id = request.json['accountID']

    job_id = request.json['jobID']

    name = request.json['candidateName']
    phone = request.json.get('phone', None)
    wechat = request.json.get('wechat', None)

    logger.info(f'candidate result: {accound_id}, {job_id}, {name}, {phone}, {wechat}')
    ret_data = {
        'status': 'ok'
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

if __name__=="__main__":
    app.run(port=2040,host="0.0.0.0",debug=True)
