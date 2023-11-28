from flask import Flask, Response, request, stream_with_context
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
import json
import math
import traceback
from datetime import datetime
from dao.tool_dao import *
import os
from utils.utils import str_is_none
# from werkzeug import secure_filename
from utils.oss import generate_thumbnail
from service.tools_service import *
from service.schedule_service import *
logger = get_logger(config['log']['log_file'])

tools_web = Blueprint('tools_web', __name__, template_folder='templates')


@tools_web.route("/backend/tools/createTask", methods=['POST'])
@web_exception_handler
def create_task():
    manage_account_id = "manage_test2"
    jd = request.form.get('jd', None)
    if jd == '' or jd is None:
        return Response(json.dumps(get_web_res_fail("jd为空")))

    if len(request.files.keys()) == 0:
        return Response(json.dumps(get_web_res_fail("上传文件为空")))
    if int(request.headers.get('Content-Length', 0)) > 10000000:
        return Response(json.dumps(get_web_res_fail("单任务不能超过10M")))
    
    filename = request.form.get('filename', None)
    if str_is_none(filename):
        return Response(json.dumps(get_web_res_fail("filename is none")))
    
    zip_file = request.files['zip_file'].read()
    file_url = generate_thumbnail(filename, zip_file)

    logger.info(f"new_resume_filter_task:{manage_account_id}, {file_url}, {int(request.headers.get('Content-Length', 0))}")
    create_new_filter_task(manage_account_id, jd, file_url)

    return Response(json.dumps(get_web_res_suc_with_data("任务创建成功")))

@tools_web.route("/backend/tools/filterTaskList", methods=['POST'])
@web_exception_handler
def filter_task_list():
    manage_account_id = 'manage_test2'
    task_list = get_filter_task_by_manage_id(manage_account_id)
    res = []
    for t in task_list:
        res.append({
            "task_id":t[0],
            "zip_name": os.path.basename(t[2]),
            "status":t[3],
            "create_time":t[4].strftime("%Y-%m-%d %H:%M:%S")
        })
    logger.info(f"filter_task_list:{manage_account_id}, {res}")
    return Response(json.dumps(get_web_res_suc_with_data(res)))

@tools_web.route("/backend/tools/filterTaskResult", methods=['POST'])
@web_exception_handler
def filter_task_result():
    manage_account_id = 'manage_test2'
    task_id = request.json.get('task_id', "")
    res = get_filter_task_by_id(task_id)
    if len(res) == 0:
        return Response(json.dumps(get_web_res_fail("task_id is wrong")))
    if res[0][1] != manage_account_id:
        return Response(json.dumps(get_web_res_fail("task_id and manage_id not match")))
    response = Response(stream_with_context(generate_csv(list(res[0]))), mimetype='text/csv')
    file_name = os.path.basename(res[0][2])
    response.headers.set("Content-Disposition", "attachment", filename=file_name)
    logger.info(f"filter_task_result_download, {manage_account_id}")
    return response


@tools_web.route("/backend/tools/execScheduleFilterTask", methods=['POST'])
@web_exception_handler
def exec_schedule_task():
    schedule_filter_task_exec()
    return