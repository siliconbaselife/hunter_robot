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
from dao.task_dao import get_job_by_id
from utils.utils import key
logger = get_logger(config['log']['log_file'])

tools_web = Blueprint('tools_web', __name__, template_folder='templates')


@tools_web.route("/backend/tools/candidateCsvByJob", methods=['GET'])
@web_exception_handler
def candidate_csv_by_job():
    job_id = request.args.get('job_id')
    manage_account_id = decrypt(request.args.get('manage_account_id', ''), key)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    ret = get_job_by_id(job_id)
    if job_id == None or manage_account_id == '' or start_date == '' or end_date == '' or len(ret) == 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    if ret[0][11] != manage_account_id:
        return Response(json.dumps(get_web_res_fail("岗位和账户不符"), ensure_ascii=False))
    platform = ret[0][1]
    if platform == 'maimai':
        response = Response(stream_with_context(generate_candidate_csv_by_job_maimai(job_id, start_date, end_date)), mimetype='text/csv')
    elif platform == 'Linkedin':
        response = Response(stream_with_context(generate_candidate_csv_by_job_Linkedin(job_id, start_date, end_date)), mimetype='text/csv')
    elif platform == 'Boss':
        response = Response(stream_with_context(generate_candidate_csv_by_job_Boss(job_id, start_date, end_date)), mimetype='text/csv')
    elif platform == 'liepin':
        response = Response(stream_with_context(generate_candidate_csv_by_job_liepin(job_id, start_date, end_date)), mimetype='text/csv')
    else:
        return Response(json.dumps(get_web_res_fail("平台不支持"), ensure_ascii=False))
    response.headers.set("Content-Disposition", "attachment", filename='result.csv')
    logger.info(f"filter_task_result_download, {manage_account_id}")
    return response




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
    
    taskname = request.form.get('taskname', None)
    filename = request.form.get('filename', None)
    if str_is_none(filename):
        return Response(json.dumps(get_web_res_fail("filename is为空"), ensure_ascii=False))
    if str_is_none(taskname):
        return Response(json.dumps(get_web_res_fail("taskname is为空"), ensure_ascii=False))

    zip_file = request.files['zip_file'].read()
    filename = str(int(time.time())) + "_" + filename
    file_url = generate_thumbnail(filename, zip_file)

    logger.info(f"new_resume_filter_task:{manage_account_id}, {file_url}, {int(request.headers.get('Content-Length', 0))}")
    create_new_filter_task(manage_account_id, jd, file_url, taskname)

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
            "taskname":t[7],
            "zip_name": os.path.basename(t[2]),
            "status":t[3],
            "create_time":t[4].strftime("%Y-%m-%d %H:%M:%S"),
            "expect_exec_time": filter_task_exec_cache.get(t[2],0)
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
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))




@tools_web.route('/backend/user/register', methods=['POST'])
@web_exception_handler
def register():
    passwd = request.json.get('passwd', '')
    email = request.json.get('email', '')
    code = request.json.get('code', '')
    invite_account = request.json.get('invite_account', '')
    logger.info(f"user_register:{email}, {passwd}, {code}, {invite_account}")
    if str_is_none(email) or str_is_none(passwd) or str_is_none(code):
        return Response(json.dumps(get_web_res_fail('信息为空'), ensure_ascii=False))
    if email not in user_code_cache or code != user_code_cache[email]:
        return Response(json.dumps(get_web_res_fail('验证码不正确'), ensure_ascii=False))

    status, msg = user_register(passwd, email, invite_account)
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


@tools_web.route("/backend/tools/downloadOnlineResume", methods=['GET'])
@web_exception_handler
def download_online_resume():
    # cookie_user_name = request.cookies.get('user_name', None)
    #插件没有domain，无法直接携带cookie
    # cookie_user_name = request.json.get('user_name', None)
    # if cookie_user_name == None:
    #     return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    # else:
    #     manage_account_id = decrypt(cookie_user_name, key)
    # if not cookie_check_service(manage_account_id):
    #     return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    manage_account_id = request.args.get('manage_account_id', '')
    platform = request.args.get('platform', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    if manage_account_id == '' or platform == '' or platform not in ('maimai', 'Linkedin') or start_date == '' or end_date == '':
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    
    if platform == 'maimai':
        response = Response(stream_with_context(generate_resume_csv_maimai(manage_account_id, platform, start_date, end_date)), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename='maimai_result.csv')
    elif platform == 'Linkedin':
        response = Response(stream_with_context(generate_resume_csv_Linkedin(manage_account_id, platform, start_date, end_date)), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename='Linkedin_result.csv')
    logger.info(f"online_resume_download, {manage_account_id}, {platform}, {start_date}, {end_date}")
    return response
    
    


@tools_web.route("/backend/tools/uploadOnlineResume", methods=['POST'])
@web_exception_handler
def upload_online_resume():
    # cookie_user_name = request.cookies.get('user_name', None)
    #插件没有domain，无法直接携带cookie
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    platform = request.json.get('platform', '')
    profile = request.json.get('profile', [])
    list_name = request.json.get('list_name', '')

    logger.info(f'upload_online_resume:{manage_account_id},{platform}, {len(profile)}, {list_name}')
    if len(profile) == 0 or platform == '' or platform not in ('maimai', 'Linkedin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    
    if platform == 'maimai':
        count = maimai_online_resume_upload_processor(manage_account_id, profile, platform)
    elif platform == 'Linkedin':
        count = linkedin_online_resume_upload_processor(manage_account_id, profile, platform, list_name)

    

    logger.info(f'upload_online_resume_exec:{manage_account_id},{platform}, {count}')
    return Response(json.dumps(get_web_res_suc_with_data('成功上传'), ensure_ascii=False))



@tools_web.route("/backend/tools/uploadOnlineResumePDF", methods=['POST'])
@web_exception_handler
def upload_online_resume_pdf():
    #插件没有domain，无法直接携带cookie
    cookie_user_name = request.form.get('user_name', None)
    if cookie_user_name is None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'manage_test'
    # candidate_id = request.form.get('candidate_id', '')
    candidate_id = manage_account_id + '_' + str(int(time.time()))
    platform = request.form.get('platform', '')
    filename = request.form.get('filename', '')
    if filename == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cv_filename = f'cv_{platform}_{filename}'
    cv_file = request.files['cv'].read()
    cv_addr = generate_thumbnail(cv_filename, cv_file)
    logger.info(f'upload_online_resume_pdf:{manage_account_id},{platform}, {filename}, {cv_addr}')
    ret = upload_online_profile_pdf(manage_account_id, platform, candidate_id, cv_addr)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@tools_web.route("/backend/tools/addResumeList", methods=['POST'])
@web_exception_handler
def add_resume_list():
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    platform = request.json.get('platform', '')
    list_name = request.json.get('list_name', '')

    if platform == '' or list_name == '':
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    ret = add_resume_list_db(manage_account_id, platform, list_name)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))


@tools_web.route("/backend/tools/getResumeList", methods=['POST'])
@web_exception_handler
def get_resume_list():
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    platform = request.json.get('platform', '')

    if platform == '':
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    ret = get_resume_list_db(manage_account_id, platform)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))




@tools_web.route("/backend/tools/resumeExist", methods=['POST'])
@web_exception_handler
def resume_exist():
    # cookie_user_name = request.cookies.get('user_name', None)
    #插件没有domain，无法直接携带cookie
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'manage_test2'

    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    logger.info(f'resume_exist:{manage_account_id},{platform}, {candidate_id}')
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    if len(get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id)) > 0:
        return Response(json.dumps(get_web_res_suc_with_data(True), ensure_ascii=False))
    else:
        return Response(json.dumps(get_web_res_suc_with_data(False), ensure_ascii=False))

@tools_web.route("/backend/conversation/report", methods=['POST'])
@web_exception_handler
def conversation_report():
# 参数格式
#{
#  "candidate_id": "aaaa",
#  "platform": "maimai",
#  "contact": {
#    "phone": "",
#    "email": "",
#    "wechat": ""
#  },
#  "conversation": [
#    {
#      "speaker": "",
#      "msg": ""
#    }
#  ]
#}
    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    contact = request.json.get('contact', '')
    conversations = request.json.get('conversations', '')
    logger.info(f'conversation report :platform = {platform}, candidate_id = {candidate_id}, contact = {contact}, conversations = {conversations}')
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or contact == '' or conversations == '':
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    create_conversation_report(candidate_id, platform, contact, conversations)
    return Response(json.dumps(get_web_res_suc_with_data(True), ensure_ascii=False))