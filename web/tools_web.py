from flask import Flask, Response, request, stream_with_context
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
import json
import math
import traceback
import time
from dao.tool_dao import *
import os
from utils.utils import str_is_none
from utils.oss import generate_thumbnail
from service.tools_service import *
from service.schedule_service import *
from service.manage_service import cookie_check_service
from utils.utils import decrypt, user_code_cache
from service.user_service import user_register, user_verify_email
logger = get_logger(config['log']['log_file'])

tools_web = Blueprint('tools_web', __name__, template_folder='templates')

key = 11

@tools_web.route("/backend/tools/createTask", methods=['POST'])
@web_exception_handler
def create_task():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    # manage_account_id = "manage_test2"
    jd = request.form.get('jd', None)
    if jd == '' or jd is None:
        return Response(json.dumps(get_web_res_fail("jd为空"), ensure_ascii=False))

    if len(request.files.keys()) == 0:
        return Response(json.dumps(get_web_res_fail("上传文件为空"), ensure_ascii=False))
    if int(request.headers.get('Content-Length', 0)) > 10000000:
        return Response(json.dumps(get_web_res_fail("单任务不能超过10M"), ensure_ascii=False))
    
    filename = request.form.get('filename', None)
    if str_is_none(filename):
        return Response(json.dumps(get_web_res_fail("filename is为空"), ensure_ascii=False))
    
    zip_file = request.files['zip_file'].read()
    filename = str(int(time.time())) + "_" + filename
    file_url = generate_thumbnail(filename, zip_file)

    logger.info(f"new_resume_filter_task:{manage_account_id}, {file_url}, {int(request.headers.get('Content-Length', 0))}")
    create_new_filter_task(manage_account_id, jd, file_url)

    return Response(json.dumps(get_web_res_suc_with_data("任务创建成功"), ensure_ascii=False))

@tools_web.route("/backend/tools/filterTaskList", methods=['POST'])
@web_exception_handler
def filter_task_list():

    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    # manage_account_id = 'manage_test2'
    task_list = get_filter_task_by_manage_id(manage_account_id)
    res = []
    for t in task_list:
        res.append({
            "task_id":t[0],
            "zip_name": os.path.basename(t[2]),
            "status":t[3],
            "create_time":t[4].strftime("%Y-%m-%d %H:%M:%S"),
            "expect_exec_time": filter_task_exec_cache.get(int(t[2]),0)
        })
    logger.info(f"filter_task_list:{manage_account_id}, {res}")
    return Response(json.dumps(get_web_res_suc_with_data(res), ensure_ascii=False))

@tools_web.route("/backend/tools/filterTaskResult", methods=['POST'])
@web_exception_handler
def filter_task_result():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    # manage_account_id = 'manage_test2'
    task_id = request.json.get('task_id', 0)
    res = get_filter_task_by_id(task_id)
    if len(res) == 0:
        return Response(json.dumps(get_web_res_fail("task_id is wrong")))
    if res[0][1] != manage_account_id:
        return Response(json.dumps(get_web_res_fail("task_id and manage_id not match")))
    if int(res[0][3]) != 2:
        return Response(json.dumps(get_web_res_fail(f"task_status_{res[0][3]}")))
    response = Response(stream_with_context(generate_csv(res)), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename='result.csv')
    logger.info(f"filter_task_result_download, {manage_account_id}")
    return response


@tools_web.route("/backend/tools/execScheduleFilterTask", methods=['POST'])
@web_exception_handler
def exec_schedule_task():
    schedule_filter_task_exec()
    return




@tools_web.route('/backend/user/register', methods=['POST'])
@web_exception_handler
def register():
    passwd = request.json.get('passwd', '')
    email = request.json.get('email', '')
    code = request.json.get('code', '')
    logger.info(f"user_register:{email}, {passwd}, {code}")
    if str_is_none(email) or str_is_none(passwd) or str_is_none(code):
        return Response(json.dumps(get_web_res_fail('信息为空'), ensure_ascii=False))
    if email not in user_code_cache or code != user_code_cache[email]:
        return Response(json.dumps(get_web_res_fail('验证码不正确'), ensure_ascii=False))

    status, msg = user_register(passwd, email)
    if status == 0:
        return Response(json.dumps(get_web_res_suc_with_data("注册成功"), ensure_ascii=False))
    else:
        return Response(json.dumps(get_web_res_fail(msg), ensure_ascii=False))

    


@tools_web.route('/backend/user/verifyEmailCode', methods=['POST'])
@web_exception_handler
def verify_email_code():
    email = request.json.get('email', '')
    if str_is_none(email):
        return Response(json.dumps(get_web_res_fail('信息为空'), ensure_ascii=False))
    
    status, msg, code = user_verify_email(email)
    if str_is_none(code):
        return Response(json.dumps(get_web_res_fail('验证码发送失败'), ensure_ascii=False))
    if status == 0:
        user_code_cache[email] = code
        logger.info(f'verify_email_code:{email}, {code}, {user_code_cache},{user_code_cache[email]}')
        return Response(json.dumps(get_web_res_suc_with_data("code已发送"), ensure_ascii=False))
    else:
        return Response(json.dumps(get_web_res_fail(msg), ensure_ascii=False))



@tools_web.route("/backend/tools/uploadOnlineResume", methods=['POST'])
@web_exception_handler
def upload_online_resume():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'manage_test2'

    platform = request.json.get('platform', '')
    profile = request.json.get('profile', [])
    logger.info(f'upload_online_resume:{manage_account_id},{platform}, {profile}')
    if len(profile) == 0 or platform == '':
        return Response(json.dumps(get_web_res_fail("参数为空"), ensure_ascii=False))
    for p in profile:
        upload_online_profile(manage_account_id, platform, json.dumps(p, ensure_ascii=False))
    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))