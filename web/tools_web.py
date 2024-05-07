from flask import Flask, Response, request, stream_with_context,send_file,after_this_request
from flask import Blueprint
import pandas as pd
import xlsxwriter
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
import json
import math
import traceback
import datetime
import time
from dao.tool_dao import *
import os
from os.path import join
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
    list_name = request.args.get('list_name', '')
    if manage_account_id == '' or platform == '' or platform not in ('maimai', 'Linkedin') or start_date == '' or end_date == '':
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    
    if platform == 'maimai':
        response = Response(stream_with_context(generate_resume_csv_maimai(manage_account_id, platform, start_date, end_date)), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename='maimai_result.csv')
    elif platform == 'Linkedin':
        response = Response(stream_with_context(generate_resume_csv_Linkedin(manage_account_id, platform, start_date, end_date, list_name)), mimetype='text/csv')
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
    min_age = request.json.get('min_age', -20000)
    max_age = request.json.get('max_age', 20000)
    tag = request.json.get('tag', '')

    logger.info(f'upload_online_resume:{manage_account_id},{platform}, {len(profile)}, {list_name}')
    if len(profile) == 0 or platform == '' or platform not in ('maimai', 'Linkedin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    
    if platform == 'maimai':
        count = maimai_online_resume_upload_processor(manage_account_id, profile, platform, tag)
    elif platform == 'Linkedin':
        count = linkedin_online_resume_upload_processor(manage_account_id, profile, platform, list_name, min_age, max_age, tag)


    logger.info(f'upload_online_resume_exec:{manage_account_id},{platform}, {count}')
    return Response(json.dumps(get_web_res_suc_with_data('成功上传'), ensure_ascii=False))

@tools_web.route("/backend/tools/filterOnlineResume", methods=['POST'])
@web_exception_handler
def filter_online_resume():
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    platform = request.json.get('platform', '')
    profile = request.json.get('profile', [])
    conditions = request.json.get('conditions', {})

    logger.info(f'filter_online_resume:{manage_account_id},{platform}, {conditions}')
    flag = True
    if platform == 'Linkedin':
        flag = linkedin_filter(manage_account_id, profile, conditions, platform)

    logger.info(f'filter_online_resume:{manage_account_id},{platform}, {flag}')
    return Response(json.dumps(get_web_res_suc_with_data({"filter": flag}), ensure_ascii=False))



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
        return Response(json.dumps(get_web_res_fail("平台不存在"), ensure_ascii=False))

    ret = get_resume_list_db(manage_account_id, platform)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@tools_web.route("/backend/tools/pluginConfig", methods=['POST'])
@web_exception_handler
def pluginConfig():
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))

    platform = request.json.get('platform', '')

    if platform == '':
        return Response(json.dumps(get_web_res_fail("平台不存在"), ensure_ascii=False))

    config_json = ''

    save_plugin_chat_config(manage_account_id, platform, config_json)

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

@tools_web.route("/backend/tools/getLeaveMsg", methods=['POST'])
@web_exception_handler
def get_leave_msg_web():
    platform = request.json.get('platform', '')
    # candidate_id = request.json.get('candidate_id', '')
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] request for leave msg for candidate_id = {}, platform = {}".format(manage_account_id, platform))
    msg = get_leave_msg(manage_account_id, platform)
    return Response(json.dumps(get_web_res_suc_with_data(msg), ensure_ascii=False))

@tools_web.route("/backend/tools/customizedGreetingScenario", methods=['POST'])
@web_exception_handler
def customized_greeting_scenario_web():
    platform = request.json.get('platform', '')
    # candidate_id = request.json.get('candidate_id', '')
    scenario = request.json.get('scenario')
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] customized_greeting_scenario_web manage_account_id = {}, platform = {}, scenario = {}".format(manage_account_id, platform, scenario))
    customized_user_scenario(manage_account_id, SCENARIO_GREETING, platform, scenario)
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))


@tools_web.route("/backend/tools/applyChatScenario", methods=['POST'])
@web_exception_handler
def apply_chat_scenario_web():
    platform = request.json.get('platform', '')
    scenario = request.json.get('scenario')
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] customized_greeting_scenario_web manage_account_id = {},  platform = {}, scenario = {}".format(manage_account_id, platform, scenario))
    msg = get_chat_scenario(manage_account_id, platform)
    return Response(json.dumps(get_web_res_suc_with_data(msg), ensure_ascii=False))

@tools_web.route("/backend/tools/customizedChatScenario", methods=['POST'])
@web_exception_handler
def customized_chat_scenario_web():
    platform = request.json.get('platform', '')
    # candidate_id = request.json.get('candidate_id', '')
    scenario = request.json.get('scenario')
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] customized_chat_scenario_web manage_account_id = {}, platform = {}, scenario = {}".format(manage_account_id, platform, scenario))
    customized_user_scenario(manage_account_id, SCENARIO_CHAT, platform, scenario)
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))

@tools_web.route("/backend/tools/createProfileTag", methods=['POST'])
@web_exception_handler
def create_profile_tag_web():
    platform = request.json.get('platform', '')
    tag = request.json.get('tag', '')
    if tag == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] create profile tag for manage_account_id = {}, platform = {}, tag = {}".format(manage_account_id, platform, tag))
    res, error_msg = create_profile_tag(manage_account_id, platform, tag)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] create profile tag for manage_account_id = {}, platform = {}, tag = {} -> res = {}".format(manage_account_id, platform, tag, res))
    return Response(json.dumps(get_web_res_suc_with_data(res), ensure_ascii=False))

@tools_web.route("/backend/tools/getTagsByUser", methods=['POST'])
@web_exception_handler
def get_tags_by_user_web():
    platform = request.json.get('platform', '')
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] get profile tag for manage_account_id = {}, platform = {}".format(manage_account_id, platform))
    res, error_msg = query_profile_tag_by_user(manage_account_id, platform)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] get profile tag for manage_account_id = {}, platform = {} -> res = {}".format(manage_account_id, platform, res))
    return Response(json.dumps(get_web_res_suc_with_data(res), ensure_ascii=False))

@tools_web.route("/backend/tools/getTagsByUserAndCandidate", methods=['POST'])
@web_exception_handler
def get_tags_by_user_and_candidate_web():
    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin'):
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] get profile tags by manage_account_id = {} and candidate_id = {}, platform = {}".format(manage_account_id, candidate_id, platform))
    tags, error_msg = query_profile_tag_relation_by_user_and_candidate(manage_account_id, candidate_id, platform)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] get profile tags by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    return Response(json.dumps(get_web_res_suc_with_data(tags), ensure_ascii=False))

@tools_web.route("/backend/tools/associateProfileTag", methods=['POST'])
@web_exception_handler
def associate_profile_tags_web():
    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    tags = request.json.get('tags', [])
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or len(tags) == 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] associate_profile_tags_web manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    _, error_msg = associate_profile_tags(manage_account_id, candidate_id, platform, tags)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] associate_profile_tags_web done by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))

@tools_web.route("/backend/tools/deassociateProfileTag", methods=['POST'])
@web_exception_handler
def deassociate_profile_tags_web():
    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    tags = request.json.get('tags', [])
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or len(tags) == 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] deassociate_profile_tags by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    _, error_msg = deassociate_profile_tags(manage_account_id, candidate_id, platform, tags)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] deassociate_profile_tags tags done by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))

@tools_web.route("/backend/tools/deleteProfileTag", methods=['POST'])
@web_exception_handler
def delete_profile_tags_web():
    platform = request.json.get('platform', '')
    candidate_id = request.json.get('candidate_id', '')
    tags = request.json.get('tags', [])
    if candidate_id == '' or platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or len(tags) == 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] delete profile tags by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    _, error_msg = delete_profile_tags(manage_account_id, candidate_id, platform, tags)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] delete profile tags done by manage_account_id = {} and candidate_id = {}, platform = {}, tags = {}".format(manage_account_id, candidate_id, platform, tags))
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))

@tools_web.route("/backend/tools/searchProfileInfoByTag", methods=['POST'])
@web_exception_handler
def search_profile_by_tag_web():
    platform = request.json.get('platform', '')
    tags = request.json.get('tags', [])
    page = request.json.get('page', 1)
    limit = request.json.get('limit', 20)
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or len(tags) == 0 or page <= 0 or limit <= 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] search profile by tag manage_account_id = {}, platform = {}, tags = {}".format(manage_account_id, platform, tags))
    data, error_msg = search_profile_by_tag(manage_account_id, platform, tags, page, limit, False)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    logger.info("[backend_tools] get profile tag done for manage_account_id = {}, platform = {}, tags = {} -> res = {}".format(manage_account_id, platform, tags, data))
    return Response(json.dumps(get_web_res_suc_with_data(data), ensure_ascii=False))

def data_to_excel_file(file_path, titles, data):
    try:
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        title_formatter = workbook.add_format()
        title_formatter.set_border(1)
        title_formatter.set_bg_color('#cccccc')
        title_formatter.set_align('center')
        title_formatter.set_bold()

        row_formatter = workbook.add_format()
        row_formatter.set_border(1)

        worksheet.write_row('A1', titles, title_formatter)
        count = 2

        for row in data:
            worksheet.write_row('A{}'.format(count), row, row_formatter)
            count += 1
    except BaseException as e:
        logger.error("[backend_tools] data to excel error {}", e)
        logger.error(traceback.format_exc())
    finally:
        workbook.close()

@tools_web.route("/backend/tools/downloadProfileInfoByTag", methods=['POST'])
@web_exception_handler
def download_profile_by_tag_web():
    platform = request.json.get('platform', '')
    tags = request.json.get('tags', [])
    page = request.json.get('page', 1)
    limit = request.json.get('limit', 9999)
    if platform == '' or platform not in ('maimai', 'Boss', 'Linkedin', 'liepin') or len(tags) == 0 or page <= 0 or limit <= 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    cookie_user_name = request.json.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    logger.info("[backend_tools] download_profile_by_tag_web manage_account_id = {}, platform = {}, tags = {}".format(manage_account_id, platform, tags))
    search_datas, error_msg = search_profile_by_tag(manage_account_id, platform, tags, page, limit, True)
    if error_msg:
        return Response(json.dumps(get_web_res_fail(error_msg), ensure_ascii=False))
    titles = []
    excel_data = []
    search_datas = search_datas['details']
    logger.info('[backend_tools] search_datas = {}', len(search_datas))
    if len(search_datas) > 0:
        for k in search_datas[0]:
            titles.append(k)
        for search_data in search_datas:
            row = []
            for k in search_data:
                row.append(search_data[k])
            excel_data.append(row)
    cur_time = datetime.datetime.now()
    file_path = join('tmp', '{}-{}.xls'.format(manage_account_id, cur_time.strftime("%Y-%m-%d-%H-%M-%S")))
    data_to_excel_file(file_path, titles, excel_data)
    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
        except Exception as error:
            logger.error("[backend_tools] error remove file {}".format(file_path))
        return response
    return send_file(file_path, as_attachment=True)

