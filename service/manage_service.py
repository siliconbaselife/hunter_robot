from dao.task_dao import *
from dao.manage_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime

def login_check_service(user_name, password):
    user_info = login_check_db(user_name)
    if len(user_info) == 0:
        return False, "用户不存在"
    if user_info[0][1] == password:
        return True, "登录成功"
    else:
        return False, "用户名密码错误"
def cookie_check_service(user_name):
    user_info = login_check_db(user_name)
    if len(user_info) == 0:
        return False
    else:
        return True

def job_mapping_service(account_id, job_id):
    jobs = jobs_query(account_id)
    jobs.append(job_id)
    jobs_ret = list(set(jobs))
    jobs_update(json.dumps(jobs_ret), account_id)
    return jobs_ret

def my_job_list_service(manage_account_id):
    jobs_db = my_job_list_db(manage_account_id)
    ret_list = []
    
    for j_d in jobs_db:
        logger.info(f"error: {j_d[3]}")
        job_config = {} if j_d[3] == None or j_d[3] == "None" else json.loads(j_d[3])
        job = {
            "job_id": j_d[0],
            "job_name": j_d[1],
            "share": j_d[2],
            "job_config": job_config
        }
        ret_list.append(job)
    return ret_list

def account_config_update_service(manage_account_id, account_id, task_config):
    job_list = []
    task_config_list = json.loads(task_config)
    for t in task_config_list:
        job_list.append(t['jobID'])
    return account_config_update_db(manage_account_id, account_id, json.dumps(task_config,ensure_ascii=False), json.dumps(job_list, ensure_ascii=False))
    

def my_account_list_service(manage_account_id):
    accounts_db = my_account_list_db(manage_account_id)
    ret_list = []
    for a_d in accounts_db:
        jobs = json.loads(a_d[3])
        jobs_ret = []
        for job_id in jobs:
            job_db = get_job_by_id(job_id)[0]
            job = {
                "job_id": job_db[0],
                "job_name": job_db[3],
                "share": job_db[9],
                "job_config": {} if job_db[6] is None or job_db[6] == "None" else json.loads(job_db[6])
            }
            jobs_ret.append(job)
        account = {
            "account_id": a_d[0],
            "platform_type": a_d[1],
            "description": a_d[2],
            "jobs":jobs_ret,
            "task_config": {} if a_d[4] is None or a_d[4] == "None" else json.loads(a_d[4])
        }
        ret_list.append(account)
    return ret_list

def candidate_list_service(job_id, start, limit):
    chat_list = get_chats_by_job_id(job_id, start, limit)
    res_chat_list = []
    for chat in chat_list:
        candidate_info = query_candidate_by_id(chat[2])
        if len(candidate_info) == 0:
            candidate_info_detail = {}
        else:
            candidate_info_detail = candidate_info[0][7]

        if chat[4] == None or chat[4] == 'NULL' or chat[4] == 'None':
            source = 'search'
        else:
            source = chat[4]
        if chat[7] == None or chat[7] == 'NULL' or chat[7] == 'None':
            detail = '[]'
        else:
            detail = chat[7]

        res_chat = {
            "candidate_id": chat[2],
            "candidate_name": chat[3],
            "source":source,
            "contact":chat[6],
            "details":detail,
            "candidate_info_detail": candidate_info_detail,
            "update_time":chat[10].strftime("%Y-%m-%d %H:%M:%S")
        }
        res_chat_list.append(res_chat)
    
    chat_sum = get_chats_num_by_job_id(job_id)[0][0]
    return chat_sum, res_chat_list

def update_job_config_service(job_id, touch_msg, filter_args):
    job_config = json.loads(get_job_by_id(job_id)[0][6])
    job_config['touch_msg'] = touch_msg
    job_config['filter_args'] = filter_args
    return update_job_config(job_id, json.dumps(job_config, ensure_ascii=False))
