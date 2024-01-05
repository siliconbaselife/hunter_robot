from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
import json
import math
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail

from utils.utils import encrypt, decrypt, generate_random_digits,str_is_none, get_stat_id_dict
from utils.utils import key

from service.manage_service_v2 import *
from service.manage_service import cookie_check_service
from service.task_service import get_undo_task
from dao.manage_dao import update_hello_ids, get_hello_ids, hello_sent

manage_web_v2 = Blueprint('manage_web_v2', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@manage_web_v2.route("/backend/manage/plugin/helloSent", methods=['POST'])
@web_exception_handler
def hello_sent():
    cookie_user_name = request.json.get('user_name', None)
    # cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    candidate_ids = request.json.get('candidate_ids', [])
    if len(candidate_ids) == 0:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    ret = hello_sent(manage_account_id, candidate_ids)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@manage_web_v2.route("/backend/manage/plugin/updateIds", methods=['POST'])
@web_exception_handler
def plugin_update_ids():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    candidate_ids = request.json.get('candidate_ids', {})
    merge_ids = []
    merge_ids.extend(candidate_ids.get('maimai', []))
    merge_ids.extend(candidate_ids.get('Boss', []))
    merge_ids.extend(candidate_ids.get('Linkedin', []))
    ret = update_hello_ids(manage_account_id, merge_ids)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@manage_web_v2.route("/backend/manage/plugin/getHelloIds", methods=['POST'])
@web_exception_handler
def plugin_get_hello_ids():
    cookie_user_name = request.json.get('user_name', None)
    # cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    platform = request.json.get('platform', "")

    if platform not in ['Linkedin', 'Boss', 'maimai'] or platform == '':
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))

    candidate_ids = request.json.get('candidate_ids', [])
    if len(candidate_ids) == 0:
        return Response(json.dumps(get_web_res_fail("无待打招呼人员"), ensure_ascii=False))

    ret = get_hello_ids(manage_account_id, platform)

    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))


@manage_web_v2.route("/recruit/account/task/fetch/v2", methods=['POST'])
@web_exception_handler
def task_fetch_api():
    account_id = request.json['accountID']
    job_id = request.json.get('jobID', "")
    logger.info(f'account_task_fetch_request_v2, {account_id}, {job_id}')
    task_list = get_undo_task(account_id, job_id, 'v2')

    logger.info(f'account_task_fetch_v2,{account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@manage_web_v2.route("/backend/manage/account/register/v2", methods=['POST'])
@web_exception_handler
def register_account_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    
    # manage_account_id = 'xt.test'

    platform_type = request.json['platformType']
    platform_id = request.json['platformID']
    jobs = []
    task_config = []
    ver = 'v2'
    account_name = request.json['account_name']
    logger.info(f'new_account_request_v2: {manage_account_id}, {platform_type} {platform_id} {account_name}')
    account_id = f'account_{platform_type}_{platform_id}'

    delete_account_by_id(account_id)
    register_account_db_v2(account_id, platform_type, platform_id, json.dumps(jobs, ensure_ascii=False), json.dumps(task_config, ensure_ascii=False), account_name, manage_account_id, ver)
    logger.info(f'new_account_register_v2: {manage_account_id}, {platform_type}, {platform_id}, {jobs}, {account_name},{account_id}, {task_config}')
    ret_data = {
        'accountID': account_id
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))


@manage_web_v2.route("/backend/manage/myAccountList/v2", methods=['POST'])
@web_exception_handler
def my_account_list_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_ret = my_account_list_service_v2(manage_account_id)
    logger.info(f'account_list_query_result_v2:{manage_account_id}, {account_ret}')
    return Response(json.dumps(get_web_res_suc_with_data(account_ret), ensure_ascii=False))


@manage_web_v2.route("/backend/manage/taskUpdate/v2", methods=['POST'])
@web_exception_handler
def task_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json['account_id']
    platform = request.json['platform']
    params = request.json['params']

    logger.info(f'task_update_request_v2:{manage_account_id}, {account_id},{platform}, {params}')
    update_config_service_v2(manage_account_id, account_id, platform, params)

    return Response(json.dumps(get_web_res_suc_with_data(''), ensure_ascii=False))


@manage_web_v2.route("/backend/manage/taskActive/v2", methods=['POST'])
@web_exception_handler
def task_active_update_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json.get('account_id', '')
    job_id = request.json.get('job_id', '')
    active = request.json.get('active', -1)
    if account_id == '' or job_id == '' or active not in [0, 1]:
        return Response(json.dumps(get_web_res_fail("参数错误"), ensure_ascii=False))
    logger.info(f'task_active_update_api:{manage_account_id}, {account_id}, {job_id}, {active}')
    flag = update_task_active(manage_account_id, account_id, job_id, active)
    return Response(json.dumps(get_web_res_suc_with_data(flag), ensure_ascii=False))


@manage_web_v2.route("/backend/manage/deleteTask/v2", methods=['POST'])
@web_exception_handler
def delete_task_api():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name == None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        manage_account_id = decrypt(cookie_user_name, key)
    if not cookie_check_service(manage_account_id):
        return Response(json.dumps(get_web_res_fail("用户不存在"), ensure_ascii=False))
    # manage_account_id = 'xt.test'
    account_id = request.json['account_id']
    job_id = request.json['job_id']
    template_id = request.json['template_id']
    logger.info(f'task_update_request:{manage_account_id}, {account_id}, {job_id}, {template_id}')

    ret = delete_config_v2(manage_account_id, account_id, job_id, template_id)

    return Response(json.dumps(get_web_res_suc_with_data(ret)))






@manage_web_v2.route("/backend/manage/metaConfig/v2", methods=['POST'])
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
        "maimai":{
            "task_config":{
                "industry":{
                    "config_type":"multi_input"
                },
                "location":{
                    "config_type":"multi_input"
                },
                "education":{
                    "config_type":"single_choice",
                    "choice_enum":[
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
                }
            },
            "job_config":{
                "min_degree":{
                    "config_type":"single_choice",
                     "choice_enum":[
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
                "school":{
                    "config_type":"single_choice",
                    "choice_enum":[
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
                },
                "neg_company":{
                    "config_type":"multi_input"
                },
                "ex_company":{
                    "config_type":"multi_input"
                },
                "job_tags":{
                    "config_type":"multi_input"
                },
                "neg_words":{
                    "config_type":"multi_input"
                }
            }
        },
        "Linkedin":{
            "task_config":{
                "industry":{
                    "config_type":"multi_input"
                },
                "location":{
                    "config_type":"multi_input"
                },
                "ex_company":{
                    "config_type":"multi_input"
                },
                "cur_company":{
                    "config_type":"multi_input"
                }
            },
            "job_config":{
                "min_degree":{
                    "config_type":"single_choice",
                    "choice_enum":[
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
                "ex_company":{
                    "config_type":"multi_input"
                },
                "neg_company":{
                    "config_type":"multi_input"
                },
                "job_tags":{
                    "config_type":"multi_input"
                },
                "neg_words":{
                    "config_type":"multi_input"
                },
                "languages":{
                    "config_type":"multi_input"
                }
            }
        },
        "Boss":{
            "task_config":{
                "location":{
                    "config_type":"multi_input"
                },
                "education":{
                    "config_type":"multi_choice",
                    "choice_enum":[
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
                "pay":{
                    "config_type":"single_choice",
                    "choice_enum":[
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
                "status":{
                    "config_type":"multi_choice",
                    "choice_enum":[
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
                },
                "work_time":{
                    "config_type":"multi_choice",
                    "choice_enum":[
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
                }
            },
            "job_config":{
                "min_degree":{
                    "min_degree":"single_choice",
                    "choice_enum":[{
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
                    }]
                },
                "school":{
                    "config_type":"single_choice",
                    "choice_enum":[
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
                },
                "ex_company":{
                    "config_type":"multi_input"
                },
                "neg_company":{
                    "config_type":"multi_input"
                },
                "job_tags":{
                    "config_type":"multi_input"
                },
                "neg_words":{
                    "config_type":"multi_input"
                }
            }
        }
        
    }


    return Response(json.dumps(get_web_res_suc_with_data(a), ensure_ascii=False))


