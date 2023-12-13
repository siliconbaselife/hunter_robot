from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.group_msg import send_candidate_info
from utils.utils import format_time,get_api_conifg
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.utils import encrypt, decrypt, generate_random_digits,str_is_none, get_stat_id_dict
from dao.task_dao import *
from service.task_service import generate_task
from service.manage_service import *

import json
import math
import traceback
from datetime import datetime

manage_web = Blueprint('manage_web', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

key = 11


@manage_web.route("/recruit/candidate/list", methods=['GET'])
@web_exception_handler
def candidate_list_web():
    job_id = request.args.get('job_id')
    page_num = request.args.get('page_num')
    limit = request.args.get('limit')
    if job_id == None or page_num == None or limit == None:
        logger.info(f'candidade_list_bad_request: job_id: {job_id}， page_num {page_num}')
        return Response(json.dumps(get_web_res_fail("no args")))

    limit = int(limit)
    page_num = int(page_num)

    logger.info(f'candidade_list: job_id: {job_id}， page_num {page_num}')
    start = limit * (page_num - 1)
    
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

@manage_web.route("/backend/manage/job/register", methods=['POST'])
@web_exception_handler
def register_job_api():
    platform_type = request.json['platformType']
    # platform_id = request.json['platformID']
    platform_id = str(generate_random_digits(10))
    job_name = request.json['jobName']
    jd = request.json.get('jobJD', "")
    robot_api = request.json.get('robotApi',"")
    job_config = request.json.get('jobConfig', None)
    robot_template = request.json.get('robotTemplate', "")
    custom_filter = int(request.json.get('customFilter', 0))
    # share = request.json['share']
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}, {manage_account_id}, {robot_template}')

    ##给字段设定默认值
    share = 0
    job_config = {}
    job_config['custom_filter'] = custom_filter
    if custom_filter == 0:
        job_config['filter_config'] = config['job_register'][platform_type]["filter_config"]
    else:
        job_config['filter_config'] = config['job_register'][platform_type]["custom_filter_config"]
    job_config['chat_config'] = config['job_register'][platform_type]["chat_config"]
    job_config['recall_config'] = config['job_register'][platform_type]["recall_config"]
    manage_config = json.loads(get_manage_config_service(manage_account_id))
    job_config['group_msg'] = manage_config['group_msg']



    logger.info(f'new job request: {platform_type} {platform_id} {job_name} {robot_api} {job_config}, {share}, {manage_account_id},{robot_template}')
    if job_config is not None:
        job_config = json.dumps(job_config, ensure_ascii=False)
    
    job_id = f'job_{platform_type}_{platform_id}'
    register_job_db(job_id, platform_type, platform_id, job_name, jd, robot_api, job_config, share, manage_account_id,robot_template)
    ret_data = {
        'jobID': job_id
    }
    logger.info(f'new job register: {platform_type} {platform_id} {job_name} {robot_api} {job_config}  {job_id}, {share}, {manage_account_id}')
    return Response(json.dumps(get_web_res_suc_with_data(ret_data), ensure_ascii=False))


@manage_web.route("/backend/manage/account/register", methods=['POST'])
@web_exception_handler
def register_account_api():
    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    jobs = request.json.get('jobs', [])
    task_config = request.json.get('taskConfig', None)
    desc = request.json.get('desc', None)
    logger.info(f'new account request: {platform_type} {platform_id} {jobs} {desc} {task_config}, {manage_account_id}')
    account_id = f'account_{platform_type}_{platform_id}'

    if task_config is None:
        task_config = generate_task(jobs)
    account_id = register_account_db(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), desc, manage_account_id)
    logger.info(f'new account register: {platform_type} {platform_id} {jobs} {desc}: {account_id} {task_config}, {manage_account_id}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@manage_web.route("/backend/manage/login", methods=['POST'])
@web_exception_handler
def manage_account_login_api():
    user_name = request.json['user_name']
    password = request.json['password']
    logger.info(f'manage_account_login: {user_name}, {password}')
    flag, msg = login_check_service(user_name, password)
    encode_user_name = encrypt(user_name, key)
    resp =  Response(json.dumps(get_web_res_suc_with_data(
        {
            "login_ret": flag,
            "errMsg": msg,
            "user_name":encode_user_name
        }
    ), ensure_ascii=False))
    if flag:
        resp.set_cookie('user_name', encode_user_name, max_age=None)
    return resp

# @manage_web.route("/backend/manage/jobMapping", methods=['POST'])
# @web_exception_handler
# def job_mapping():
#     cookie_user_name = request.cookies.get('user_name', None)
#     if cookie_user_name == None:
#         return Response(json.dumps(get_web_res_fail("未登录")))
#     else:
#         manage_account_id = decrypt(cookie_user_name, key)
#     if not cookie_check_service(manage_account_id):
#         return Response(json.dumps(get_web_res_fail("用户不存在")))
#     # manage_account_id = request.json['manage_account_id']
#     account_id = request.json['account_id']
#     job_id = request.json['job_id']
#     logger.info(f'job_mapping: {manage_account_id}, {account_id}, {job_id}')
#     ret = job_mapping_service(account_id, job_id)
#     return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/myJobList", methods=['POST'])
@web_exception_handler
def my_job_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    job_ret = my_job_list_service(manage_account_id)
    logger.info(f'job_list_query_result:{manage_account_id}, {job_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(job_ret), ensure_ascii=False))

@manage_web.route("/backend/manage/myAccountList", methods=['POST'])
@web_exception_handler
def my_account_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = request.json['manage_account_id']
    account_ret = my_account_list_service(manage_account_id)
    logger.info(f'account_list_query_result:{manage_account_id}, {account_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(account_ret), ensure_ascii=False))

@manage_web.route("/backend/manage/accountUpdate", methods=['POST'])
@web_exception_handler
def account_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录")))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在")))
    # manage_account_id = request.json['manage_account_id']
    account_id = request.json['account_id']
    task_config = request.json['task_config']
    logger.info(f'account_update_request:{manage_account_id}, {account_id}, {task_config}')
    ret = account_config_update_service(manage_account_id, account_id, task_config)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))


@manage_web.route("/backend/manage/jobUpdate", methods=['POST'])
@web_exception_handler
def job_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    job_id = request.json['job_id']
    robot_api = request.json.get('robot_api', "")
    touch_msg = request.json['touch_msg']
    filter_args = request.json.get('filter_args', {})
    robot_template_id = request.json.get('robot_template', "")
    custom_filter_content = request.json.get('custom_filter_content', '')
    if 'neg_words' not in filter_args or ('neg_words' in filter_args and str_is_none(filter_args['neg_words'])):
        filter_args['neg_words'] = []
    if 'ex_company' not in filter_args or ('ex_company' in filter_args and str_is_none(filter_args['ex_company'])):
        filter_args['ex_company'] = []
    if 'cur_company' not in filter_args or ('cur_company' in filter_args and str_is_none(filter_args['cur_company'])):
        filter_args['cur_company'] = []
    
    logger.info(f'job_update_request:{job_id}, {touch_msg}, {filter_args},{robot_api},{robot_template_id},{custom_filter_content}')
    ret = update_job_config_service(job_id, touch_msg, filter_args, robot_api, robot_template_id, custom_filter_content)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/taskUpdate", methods=['POST'])
@web_exception_handler
def task_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    account_id = request.json['account_id']
    task_config = request.json['task_config']
    logger.info(f'task_update_request:{manage_account_id}, {account_id}, {task_config}')

    ret = update_task_config_service(manage_account_id, account_id, task_config)

    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/deleteTask", methods=['POST'])
@web_exception_handler
def delete_task_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = "manage_test"
    account_id = request.json['account_id']
    job_id = request.json['job_id']
    logger.info(f'task_update_request:{manage_account_id}, {account_id}, {job_id}')

    ret = delete_task(manage_account_id, account_id, job_id)

    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/templateUpdate", methods=['POST'])
@web_exception_handler
def template_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    template_id = request.json['template_id']
    template_name = request.json['template_name']
    template_config = request.json['template_config']
    logger.info(f'template_update:{manage_account_id},{template_id}, {template_name}, {template_config}')
    ret = template_update_service(manage_account_id, template_id, template_name, template_config)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/templateInsert", methods=['POST'])
@web_exception_handler
def template_insert_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # template_id = request.json['template_id']
    template_name = request.json['template_name']
    template_config = request.json['template_config']
    template_id = manage_account_id + "_" + template_name
    logger.info(f'template_insert:{manage_account_id},{template_id}, {template_name}, {template_config}')
    ret = template_insert_service(manage_account_id, template_id, template_name, template_config)
    return Response(json.dumps(get_web_res_suc_with_data(ret)))

@manage_web.route("/backend/manage/templateList", methods=['POST'])
@web_exception_handler
def template_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    ret = template_list_service(manage_account_id)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@manage_web.route("/backend/manage/metaConfig", methods=['POST'])
@web_exception_handler
def meta_config():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    a = {
        "platform_type":["Boss", "Linkedin", "maimai"],
        "filter_config":[{
            "platform": "Boss",
            "account_meta_config":[
                {
                    "config_name":"每天打招呼总数",
                    "config_value":"helloSum",
                    "type":"input"
                },{
                    "config_name":"打招呼策略",
                    "config_value":"timeMount",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":[{"time": "09:00", "mount": 100}],
                            "label":"9点100%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 50},{"time": "20:00", "mount": 50}],
                            "label":"9/20各50%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 25},{"time": "12:00", "mount": 25},{"time": "17:00", "mount": 25},{"time": "20:00", "mount": 25}],
                            "label":"9/12/17/20各25%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 10},{"time": "10:00", "mount": 10},{"time": "11:00", "mount": 10},{"time": "12:00", "mount": 10},{"time": "13:00", "mount": 10},{"time": "14:00", "mount": 10},{"time": "15:00", "mount": 10},{"time": "16:00", "mount": 10},{"time": "17:00", "mount": 10},{"time": "18:00", "mount": 10}],
                            "label":"9-18每小时10%"
                        }
                    ]
                },
                {
                    "config_name":"地域",
                    "config_value":"locations",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"北京",
                            "label":"北京"
                        },
                        {
                            "value":"上海",
                            "label":"上海"
                        },
                        {
                            "value":"天津",
                            "label":"天津"
                        },
                        {
                            "value":"深圳",
                            "label":"深圳"
                        },
                        {
                            "value":"石家庄",
                            "label":"石家庄"
                        },
                        {
                            "value":"成都",
                            "label":"成都"
                        },
                        {
                            "value":"杭州",
                            "label":"杭州"
                        },
                        {
                            "value":"武汉",
                            "label":"武汉"
                        },
                        {
                            "value":"广州",
                            "label":"广州"
                        },
                        {
                            "value":"苏州",
                            "label":"苏州"
                        },
                        {
                            "value":"珠海",
                            "label":"珠海"
                        },
                        {
                            "value":"宁波",
                            "label":"宁波"
                        },
                        {
                            "value":"东莞",
                            "label":"东莞"
                        }
                    ]
                }
                ,{
                    "config_name":"教育水平",
                    "config_value":"education",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"初中及以下",
                            "label":"初中及以下"
                        },
                        {
                            "value":"中专/中技",
                            "label":"中专/中技"
                        },
                        {
                            "value":"高中",
                            "label":"高中"
                        },
                        {
                            "value":"大专",
                            "label":"大专"
                        },
                        {
                            "value":"本科",
                            "label":"本科"
                        },
                        {
                            "value":"硕士",
                            "label":"硕士"
                        },
                        {
                            "value":"博士",
                            "label":"博士"
                        }
                    ]
                },
                {
                    "config_name":"薪资范围",
                    "config_value":"pay",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"3K以下",
                            "label":"3K以下"
                        },
                        {
                            "value":"3-5K",
                            "label":"3-5K"
                        },
                        {
                            "value":"5-10K",
                            "label":"5-10K"
                        },
                        {
                            "value":"10-20K",
                            "label":"10-20K"
                        },
                        {
                            "value":"20-50K",
                            "label":"20-50K"
                        },
                        {
                            "value":"50K以上",
                            "label":"50K以上"
                        }
                    ]
                },
                {
                    "config_name":"人选状态",
                    "config_value":"status",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"离职-随时到岗",
                            "label":"离职-随时到岗"
                        },
                        {
                            "value":"在职-暂不考虑",
                            "label":"在职-暂不考虑"
                        },
                        {
                            "value":"在职-考虑机会",
                            "label":"在职-考虑机会"
                        },
                        {
                            "value":"在职-月内到岗",
                            "label":"在职-月内到岗"
                        }
                    ]
                }
            ],
            "job_meta_config": [
                {
                    "config_name":"问候信息",
                    "config_value":"touchMsg",
                    "type":"input"
                },
                {
                    "config_name":"年龄范围",
                    "config_value":"age_range",
                    "type":"range"
                },
                {
                    "config_name":"最低学历",
                    "config_value":"min_degree",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"初中及以下",
                            "label":"初中及以下"
                        },
                        {
                            "value":"中专",
                            "label":"中专"
                        },
                        {
                            "value":"高中",
                            "label":"高中"
                        },
                        {
                            "value":"大专",
                            "label":"大专"
                        },
                        {
                            "value":"本科",
                            "label":"本科"
                        },
                        {
                            "value":"硕士",
                            "label":"硕士"
                        },
                        {
                            "value":"博士",
                            "label":"博士"
                        }
                    ]
                },
                {
                    "config_name":"地点",
                    "config_value":"location",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"北京",
                            "label":"北京"
                        },
                        {
                            "value":"上海",
                            "label":"上海"
                        },
                        {
                            "value":"天津",
                            "label":"天津"
                        },
                        {
                            "value":"深圳",
                            "label":"深圳"
                        },
                        {
                            "value":"石家庄",
                            "label":"石家庄"
                        },
                        {
                            "value":"成都",
                            "label":"成都"
                        },
                        {
                            "value":"杭州",
                            "label":"杭州"
                        },
                        {
                            "value":"武汉",
                            "label":"武汉"
                        },
                        {
                            "value":"广州",
                            "label":"广州"
                        },
                        {
                            "value":"苏州",
                            "label":"苏州"
                        },
                        {
                            "value":"珠海",
                            "label":"珠海"
                        },
                        {
                            "value":"宁波",
                            "label":"宁波"
                        },
                        {
                            "value":"东莞",
                            "label":"东莞"
                        }
                    ]
                },{
                    "config_name":"关键词",
                    "config_value":"job_tags",
                    "type":"multi_input"
                },{
                    "config_name":"负向关键词（例如招聘公司）",
                    "config_value":"neg_words",
                    "type":"multi_input"
                },{
                    "config_name":"活跃时间",
                    "config_value":"active_threshold",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"60",
                            "label":"一小时之内"
                        },
                        {
                            "value":"180",
                            "label":"三小时之内"
                        },
                        {
                            "value":"1440",
                            "label":"一天之内"
                        },
                        {
                            "value":"10080",
                            "label":"一周之内"
                        },
                        {
                            "value":"500000",
                            "label":"无限制"
                        }
                    ]
                }, {
                    "config_name":"学历附加",
                    "config_value":"school",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"0",
                            "label":"无要求"
                        },
                        {
                            "value":"1",
                            "label":"211学校"
                        },
                        {
                            "value":"2",
                            "label":"985学校"
                        }
                    ]
                }
            ]
        }, {
            "platform": "maimai",
            "account_meta_config":[
                {
                    "config_name":"每天打招呼总数",
                    "config_value":"helloSum",
                    "type":"input"
                },{
                    "config_name":"打招呼策略",
                    "config_value":"timeMount",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":[{"time": "09:00", "mount": 100}],
                            "label":"9点100%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 50},{"time": "20:00", "mount": 50}],
                            "label":"9/20各50%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 25},{"time": "12:00", "mount": 25},{"time": "17:00", "mount": 25},{"time": "20:00", "mount": 25}],
                            "label":"9/12/17/20各25%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 10},{"time": "10:00", "mount": 10},{"time": "11:00", "mount": 10},{"time": "12:00", "mount": 10},{"time": "13:00", "mount": 10},{"time": "14:00", "mount": 10},{"time": "15:00", "mount": 10},{"time": "16:00", "mount": 10},{"time": "17:00", "mount": 10},{"time": "18:00", "mount": 10}],
                            "label":"9-18每小时10%"
                        }
                    ]
                },
                {
                    "config_name":"学历",
                    "config_value":"education",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"专科及以上",
                            "label":"专科及以上"
                        },
                        {
                            "value":"本科及以上",
                            "label":"本科及以上"
                        },
                        {
                            "value":"硕士及以上",
                            "label":"硕士及以上"
                        },
                        {
                            "value":"博士",
                            "label":"博士"
                        }
                    ]
                },
                {
                    "config_name":"工作年限",
                    "config_value":"worktime",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"在校",
                            "label":"在校"
                        },
                        {
                            "value":"应届",
                            "label":"应届"
                        },
                        {
                            "value":"1年以内",
                            "label":"1年以内"
                        },
                        {
                            "value":"1-3年",
                            "label":"1-3年"
                        },
                        {
                            "value":"3-5年",
                            "label":"3-5年"
                        },
                        {
                            "value":"5-10年",
                            "label":"5-10年"
                        },
                        {
                            "value":"10年以上",
                            "label":"10年以上"
                        }
                    ]
                },
                {
                    "config_name":"行业（务必用英文逗号分隔,或关系）",
                    "config_value":"industry",
                    "type":"multi_input"
                },
                {
                    "config_name":"搜索",
                    "config_value":"searchText",
                    "type":"input"
                },
                {
                    "config_name":"地域",
                    "config_value":"locations",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"无限制",
                            "label":"无限制"
                        },
                        {
                            "value":"北京",
                            "label":"北京"
                        },
                        {
                            "value":"上海",
                            "label":"上海"
                        },
                        {
                            "value":"天津",
                            "label":"天津"
                        },
                        {
                            "value":"深圳",
                            "label":"深圳"
                        },
                        {
                            "value":"石家庄",
                            "label":"石家庄"
                        },
                        {
                            "value":"成都",
                            "label":"成都"
                        },
                        {
                            "value":"杭州",
                            "label":"杭州"
                        },
                        {
                            "value":"武汉",
                            "label":"武汉"
                        },
                        {
                            "value":"广州",
                            "label":"广州"
                        },
                        {
                            "value":"苏州",
                            "label":"苏州"
                        },
                        {
                            "value":"珠海",
                            "label":"珠海"
                        },
                        {
                            "value":"宁波",
                            "label":"宁波"
                        },
                        {
                            "value":"东莞",
                            "label":"东莞"
                        }
                    ]
                }
            ],
            "job_meta_config": [
                {
                    "config_name":"问候信息",
                    "config_value":"touchMsg",
                    "type":"input"
                },
                {
                    "config_name":"年龄范围",
                    "config_value":"age_range",
                    "type":"range"
                },
                {
                    "config_name":"最低学历",
                    "config_value":"min_degree",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"初中及以下",
                            "label":"初中及以下"
                        },
                        {
                            "value":"中专",
                            "label":"中专"
                        },
                        {
                            "value":"高中",
                            "label":"高中"
                        },
                        {
                            "value":"大专",
                            "label":"大专"
                        },
                        {
                            "value":"本科",
                            "label":"本科"
                        },
                        {
                            "value":"硕士",
                            "label":"硕士"
                        },
                        {
                            "value":"博士",
                            "label":"博士"
                        }
                    ]
                },
                {
                    "config_name":"地点",
                    "config_value":"location",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"无限制",
                            "label":"无限制"
                        },
                        {
                            "value":"北京",
                            "label":"北京"
                        },
                        {
                            "value":"上海",
                            "label":"上海"
                        },
                        {
                            "value":"天津",
                            "label":"天津"
                        },
                        {
                            "value":"深圳",
                            "label":"深圳"
                        },
                        {
                            "value":"石家庄",
                            "label":"石家庄"
                        },
                        {
                            "value":"成都",
                            "label":"成都"
                        },
                        {
                            "value":"杭州",
                            "label":"杭州"
                        },
                        {
                            "value":"武汉",
                            "label":"武汉"
                        },
                        {
                            "value":"广州",
                            "label":"广州"
                        },
                        {
                            "value":"苏州",
                            "label":"苏州"
                        },
                        {
                            "value":"珠海",
                            "label":"珠海"
                        },
                        {
                            "value":"宁波",
                            "label":"宁波"
                        },
                        {
                            "value":"东莞",
                            "label":"东莞"
                        }
                    ]
                },{
                    "config_name":"曾任职公司（务必用英文逗号分隔,或关系）",
                    "config_value":"ex_company",
                    "type":"multi_input"
                },{
                    "config_name":"现任职公司（务必用英文逗号分隔,或关系）",
                    "config_value":"cur_company",
                    "type":"multi_input"
                },
                {
                    "config_name":"关键词",
                    "config_value":"job_tags",
                    "type":"multi_input"
                },
                {
                    "config_name":"负向关键词（例如招聘公司）",
                    "config_value":"neg_words",
                    "type":"multi_input"
                },
                {
                    "config_name":"活跃时间",
                    "config_value":"active_threshold",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"60",
                            "label":"一小时之内"
                        },
                        {
                            "value":"180",
                            "label":"三小时之内"
                        },
                        {
                            "value":"1440",
                            "label":"一天之内"
                        },
                        {
                            "value":"10080",
                            "label":"一周之内"
                        },
                        {
                            "value":"500000",
                            "label":"无限制"
                        }
                    ]
                }, {
                    "config_name":"学历附加",
                    "config_value":"school",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"0",
                            "label":"无要求"
                        },
                        {
                            "value":"1",
                            "label":"211学校"
                        },
                        {
                            "value":"2",
                            "label":"985学校"
                        }
                    ]
                }
            ],
            "one_time_meta_config":[
                {
                    "config_name":"具体发送的信息",
                    "config_value":"msg",
                    "type":"input"
                },
                {
                    "config_name":"关键词搜索",
                    "config_value":"keyword",
                    "type":"input"
                },
                {
                    "config_name":"最低学历",
                    "config_value":"min_degree",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":"初中及以下",
                            "label":"初中及以下"
                        },
                        {
                            "value":"中专",
                            "label":"中专"
                        },
                        {
                            "value":"高中",
                            "label":"高中"
                        },
                        {
                            "value":"大专",
                            "label":"大专"
                        },
                        {
                            "value":"本科",
                            "label":"本科"
                        },
                        {
                            "value":"硕士",
                            "label":"硕士"
                        },
                        {
                            "value":"博士",
                            "label":"博士"
                        }
                    ]
                },
                {
                    "config_name":"地点",
                    "config_value":"location",
                    "type":"multi_choice",
                    "enum": [
                        {
                            "value":"无限制",
                            "label":"无限制"
                        },
                        {
                            "value":"北京",
                            "label":"北京"
                        },
                        {
                            "value":"上海",
                            "label":"上海"
                        },
                        {
                            "value":"天津",
                            "label":"天津"
                        },
                        {
                            "value":"深圳",
                            "label":"深圳"
                        },
                        {
                            "value":"石家庄",
                            "label":"石家庄"
                        },
                        {
                            "value":"成都",
                            "label":"成都"
                        },
                        {
                            "value":"杭州",
                            "label":"杭州"
                        },
                        {
                            "value":"武汉",
                            "label":"武汉"
                        },
                        {
                            "value":"广州",
                            "label":"广州"
                        },
                        {
                            "value":"苏州",
                            "label":"苏州"
                        },
                        {
                            "value":"珠海",
                            "label":"珠海"
                        },
                        {
                            "value":"宁波",
                            "label":"宁波"
                        },
                        {
                            "value":"东莞",
                            "label":"东莞"
                        }
                    ]
                }
            ]
        },{
            "platform": "Linkedin",
            "account_meta_config":[
                {
                    "config_name":"每天打招呼总数",
                    "config_value":"helloSum",
                    "type":"input"
                },{
                    "config_name":"打招呼策略",
                    "config_value":"timeMount",
                    "type":"single_choice",
                    "enum": [
                        {
                            "value":[{"time": "09:00", "mount": 100}],
                            "label":"9点100%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 50},{"time": "20:00", "mount": 50}],
                            "label":"9/20各50%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 25},{"time": "12:00", "mount": 25},{"time": "17:00", "mount": 25},{"time": "20:00", "mount": 25}],
                            "label":"9/12/17/20各25%"
                        },
                        {
                            "value":[{"time": "09:00", "mount": 10},{"time": "10:00", "mount": 10},{"time": "11:00", "mount": 10},{"time": "12:00", "mount": 10},{"time": "13:00", "mount": 10},{"time": "14:00", "mount": 10},{"time": "15:00", "mount": 10},{"time": "16:00", "mount": 10},{"time": "17:00", "mount": 10},{"time": "18:00", "mount": 10}],
                            "label":"9-18每小时10%"
                        }
                    ]
                },
                {
                    "config_name":"搜索",
                    "config_value":"searchText",
                    "type":"input"
                },
                {
                    "config_name":"地域",
                    "config_value":"location",
                    "type":"input"
                },
                {
                    "config_name":"行业（务必用英文逗号分隔,或关系）",
                    "config_value":"industry",
                    "type":"multi_input"
                },
                {
                    "config_name":"曾任职公司（务必用英文逗号分隔,或关系）",
                    "config_value":"ex_company",
                    "type":"multi_input"
                },
                {
                    "config_name":"现任职公司（务必用英文逗号分隔,或关系）",
                    "config_value":"cur_company",
                    "type":"multi_input"
                }
            ],
            "job_meta_config":[
                {
                    "config_name":"问候信息",
                    "config_value":"touchMsg",
                    "type":"input"
                }
            ]
        }]
        }
    api_config = get_api_conifg(manage_account_id)
    api_config = manage_process_api_config(manage_account_id, api_config)

    # logger.info(f'test_  {a["filter_config"][0]["job_meta_config"]}')
    for i in range(0, len(a["filter_config"])):
        a["filter_config"][i]["job_meta_config"].append({
            "config_name":"语言模型",
            "config_value":"robot_api",
            "type":"single_choice",
            "enum": api_config
        })
    # logger.info(f'test_  {a["filter_config"][0]["job_meta_config"]}')
    return Response(json.dumps(get_web_res_suc_with_data(a), ensure_ascii=False))




@manage_web.route("/backend/manage/statistic", methods=['GET'])
@web_exception_handler
def get_ip():
    manage_id = request.args.get('manage_id')
    if manage_id not in get_stat_id_dict():
        return Response(json.dumps(get_web_res_fail("统计账户错误"), ensure_ascii=False))
    manage_account_list = get_stat_id_dict()[manage_id]
    ret = get_stat_service(manage_account_list)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
