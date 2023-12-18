from dao.task_dao import *
from dao.manage_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time,process_list,process_str,process_str_to_list
import copy
from datetime import datetime
from pymysql .converters import escape_string

def manage_process_api_config(manage_account_id, api_config):
    template_list = get_llm_template_by_manage_id_db(manage_account_id)
    for t in template_list:
        api_config.append({
            "label":t[0],
            "value":"/vision/chat/receive/message/chat/v1",
            "robot_template": t[1]
        })
    return api_config

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
        job_config_json = j_d[3].replace('\n', '\\n')
        # logger.info(f"error: {job_config_json}")
        job_config = {} if j_d[3] == None or j_d[3] == "None" else json.loads(job_config_json)
        job = {
            "job_id": j_d[0],
            "job_name": j_d[1],
            "share": j_d[2],
            "job_config": job_config,
            "platform_type":j_d[4],
            "robot_api":j_d[5],
            "robot_template":j_d[6]
        }
        ret_list.append(job)
    return ret_list



def account_config_update_service(manage_account_id, account_id, task_config):
    job_list = []
    for i in range(0, len(task_config)):
        time_mount_new = []
        helloSum = task_config[i]['helloSum']
        for t in task_config[i]['timeMount']:
            time_mount_new.append({
                'time': t['time'],
                'mount': int(helloSum * t['mount'] / 100)
            })
        task_config[i]['timeMount'] = time_mount_new
    for t in task_config:
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
            # job_config_json = job_db[6].replace('\n', '\\n')
            job = {
                "job_id": job_db[0],
                "job_name": job_db[3],
                "share": job_db[9],
                "robot_api": job_db[10],
                "job_config": {} if job_db[6] is None or job_db[6] == "None" else json.loads(job_db[6])
            }
            jobs_ret.append(job)
        account = {
            "account_id": a_d[0],
            "platform_type": a_d[1],
            "description": a_d[2],
            "jobs":jobs_ret,
            "task_config": [] if a_d[4] is None or a_d[4] == "None" else json.loads(a_d[4])
        }
        ret_list.append(account)
    return ret_list

def my_account_list_service_v2(manage_account_id):
    accounts_db = my_account_list_db_v2(manage_account_id, 'v2')
    ret_list = []
    for a_d in accounts_db:
        jobs = json.loads(a_d[3])
        jobs_ret = {}
        for job_id in jobs:
            job_db = get_job_by_id(job_id)[0]
            # job_config_json = job_db[6].replace('\n', '\\n')
            llm_config = json.loads(get_llm_config_by_id_db(job_db[12]))
            job = {
                "job_id": job_db[0],
                "job_name": job_db[3],
                "share": job_db[9],
                "robot_api": job_db[10],
                "job_config": {} if job_db[6] is None or job_db[6] == "None" else json.loads(job_db[6]),
                "llm_config": llm_config
            }
            jobs_ret[job_db[0]] = job
        task_config = [] if a_d[4] is None or a_d[4] == "None" else json.loads(a_d[4])
        for t in task_config:
            t['job_config'] = jobs_ret[t['jobID']]
        account = {
            "account_id": a_d[0],
            "platform_type": a_d[1],
            "description": a_d[2],
            "task_config": task_config
        }
        ret_list.append(account)
    return ret_list

def candidate_list_service(job_id, start, limit):
    chat_list = get_chats_by_job_id_with_start(job_id, start, limit)
    res_chat_list = []
    for chat in chat_list:
        candidate_info = query_candidate_by_id(chat[2])
        # logger.info(f'test: {chat}, {candidate_info}')

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





def update_job_config_service(job_id, touch_msg, filter_args, robot_api, robot_template_id, custom_filter_content):
    job_config_json = get_job_by_id(job_id)[0][6]
    if job_config_json == None or job_config_json == 'None' or job_config_json == 'NULL' or job_config_json == "":
        job_config = {}
    else:
        # job_config_json = job_config_json.replace('\n', '\\n')
        job_config = json.loads(job_config_json)
    job_config['touch_msg'] = process_str(touch_msg)
    job_config['filter_args'] = filter_args
    job_config['filter_args']['job_tags'] = process_list(job_config['filter_args']['job_tags'])
    job_config['filter_args']['neg_words'] = process_list(job_config['filter_args']['neg_words'])
    job_config['filter_args']['ex_company'] = process_list(job_config['filter_args']['ex_company'])
    job_config['filter_args']['cur_company'] = process_list(job_config['filter_args']['cur_company'])
    job_config['custom_filter_content'] = custom_filter_content
    return update_job_config(job_id,robot_api, json.dumps(job_config, ensure_ascii=False), robot_template_id)

def delete_task(manage_account_id, account_id, job_id):
    ret = get_jobs_task_by_id(account_id)
    jobs = json.loads(ret[0])
    for i in range(0, len(jobs)):
        if job_id == jobs[i]:
            jobs.pop(i)
            break
    task_config = json.loads(ret[1])
    for i in range(0, len(task_config)):
        if job_id == task_config[i]['jobID']:
            task_config.pop(i)
            break
    return account_config_update_db(manage_account_id, account_id, json.dumps(task_config, ensure_ascii=False), json.dumps(jobs))
    

def update_task_active(account_id, job_id, active):
    task_configs = json.loads(get_account_task_db(account_id))
    flag = False
    for i in range(0, len(task_configs)):
        if task_configs[i]["jobID"] == job_id:
            task_configs[i]["active"] = active
            flag = True
    return flag

def update_task_config_service(manage_account_id, account_id, task_config_dict):
    time_mount_new = []
    helloSum = task_config_dict['helloSum']
    for t in task_config_dict['timeMount']:
        time_mount_new.append({
            'time': t['time'],
            'mount': int(helloSum * t['mount'] / 100)
        })
    task_config_dict['timeMount'] = time_mount_new
    if 'industry' in task_config_dict['filter']:
        task_config_dict['filter']['industry'] = process_list(task_config_dict['filter']['industry'])
    if 'ex_company' in task_config_dict['filter']:
        task_config_dict['filter']['ex_company'] = process_list(task_config_dict['filter']['ex_company'])
    if 'cur_company' in task_config_dict['filter']:
        task_config_dict['filter']['cur_company'] = process_list(task_config_dict['filter']['cur_company'])
    # task_config_dict['filter']['searchText'] = task_config_dict['filter']['searchText'].replace("\'", "")
    # task_config_dict['filter']['searchText'] = escape_string(task_config_dict['filter']['searchText'])
    # task_config_dict['filter']['searchText'] = escape_string(task_config_dict['filter']['searchText'])
    # logger.info(f"test:{task_config_dict['filter']['searchText']}")

    task_configs = json.loads(get_account_task_db(account_id))
    flag = True
    for i in range(0, len(task_configs)):
        if task_configs[i]["taskType"] == "batchTouch" and task_configs[i]["jobID"] == task_config_dict["jobID"]:
            task_configs[i] = task_config_dict
            flag = False
    if flag:
        task_configs.append(task_config_dict)
    job_list = []
    for t in task_configs:
        job_list.append(t['jobID'])
    task_str = json.dumps(task_configs,ensure_ascii=False)
    # logger.info(f"test:{task_str}")
    task_str = task_str.replace('\\n',',')
    # logger.info(f"test:{task_str}")
    return account_config_update_db(manage_account_id, account_id, task_str, json.dumps(job_list, ensure_ascii=False))

def get_manage_config_service(manage_account_id):
    return get_manage_config_db(manage_account_id)


def template_update_service(manage_account_id, template_id, template_name, template_config):
    template_config['job_requirements'] = template_config['job_requirements'].replace('"', '“')
    template_config['job_requirements'] = template_config['job_requirements'].replace("'", '‘')
    template_config['job_description'] = template_config['job_description'].replace('"', '“')
    template_config['job_description'] = template_config['job_description'].replace("'", '‘')
    template_config['other_information'] = template_config['other_information'].replace('"', '“')
    template_config['other_information'] = template_config['other_information'].replace("'", '‘')
    template_config_p = process_str(json.dumps(template_config, ensure_ascii=False))
    return update_llm_template(template_name, template_config_p, template_id)

def template_insert_service(manage_account_id, template_id, template_name, template_config):
    template_config_p = process_str(json.dumps(template_config, ensure_ascii=False))
    return insert_llm_template(manage_account_id, template_id, template_name, template_config_p)

def template_list_service(manage_account_id):
    db_ret = get_llm_template_by_manage_id_db(manage_account_id)
    ret = []
    for dr in  db_ret:
        ret.append({
            "template_id": dr[1],
            "template_name": dr[0],
            "template_config":dr[2]
        })
    return ret


def get_stat_service(manage_account_list):
    final_ret = []
    for ma in manage_account_list:
        account_list = my_account_list_db(ma)
        account_ret = []
        for a_l in account_list:
            job_ret = []
            jobs = json.loads(a_l[3])
            logger.info(f"test_test:{jobs}")
            for j in jobs:
                j_r = get_chat_count_by_job(j)
                job_name = get_job_name_by_id(j)
                date_ret = []
                for _j_r in j_r:
                    date_ret.append({
                        "日期":str(_j_r[0]),
                        "打招呼总数":int(_j_r[1]),
                        "拿到联系方式总数":int(_j_r[2])
                    })
                job_ret.append({
                    "岗位id": j,
                    "岗位名称":job_name,
                    "招呼明细": date_ret
                })
            account_ret.append({
                "账号id": a_l[0],
                "账号名称": a_l[2],
                "账号平台": a_l[1],
                "账号结果": job_ret
            })        
        final_ret.append({
            "管理账户":ma,
            "账号运行状态":account_ret
        })
    return final_ret