from dao.task_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime

def get_id_name(candidate_info, platform_type):
    if platform_type == 'maimai':
        return candidate_info['id'], candidate_info['name']
    elif platform_type == 'Linkedin':
        return candidate_info['id'], candidate_info['profile']['name']
    elif platform_type == 'Boss':
        return candidate_info['geekCard']['geekId'], candidate_info['geekCard']['geekName']
    elif platform_type == 'liepin':
        return candidate_info['usercIdEncode'], candidate_info['showName']
    return '', ''

def process_independent_encode_multi(account_id, candidate_ids):
    independent = get_independent_by_account_id(account_id)
    ret = []
    for c in candidate_ids:
        if independent == 1:
            ret.append(account_id + "_" + c)
        else:
            ret.append(c)
    return ret

def process_independent_encode(account_id, candidate_id):
    independent = get_independent_by_account_id(account_id)
    if independent == 1:
        return account_id + "_" + candidate_id
    else:
        return candidate_id

# def process_independent_decode(candidate_id):
#     return

def filter_time(time_percent, retain_sum):
    sum = 0
    filter_time_res = []
    t_now = time.strftime("%H:%M", time.localtime())
    for t in time_percent:
        if t["time"] > t_now:
            filter_time_res.append(t)
            sum += t["mount"]
    for t in filter_time_res:
        if sum == 0:
            t["mount"] = 0
        else:
            t["mount"] = round(t["mount"] / sum * retain_sum) 
    return filter_time_res


## 处理重启后的任务的适配
def re_org_task(config_data, today_sub_task_log, job_id):
    sub_task_dict = {}
    for t in today_sub_task_log:
        sub_task_dict[t[2]] = t
    res = []
    for job_config in config_data:
        if job_id != '' and job_config["jobID"] != job_id:
            continue
        if job_config['taskType']=='batchTouch':
            retain_sum = job_config["helloSum"] - sub_task_dict[job_config["jobID"]][5]

            time_percent = job_config["timeMount"]
            time_percent_filtered = filter_time(time_percent, retain_sum)

            touch_msg = json.loads(get_job_by_id(job_config["jobID"])[0][6])["touch_msg"]

            r_job = {
                "jobID":job_config["jobID"],
                "taskType":job_config['taskType'],
                "helloSum": retain_sum,
                "timeMount":time_percent_filtered,
                "filter": job_config["filter"],
                "touch_msg": touch_msg
            }
            res.append(r_job)
    return res

def re_org_task_v2(config_data, today_sub_task_log, job_id):
    sub_task_dict = {}
    for t in today_sub_task_log:
        sub_task_dict[t[2]] = t
    res = []
    for i in range(0, len(config_data)):
        if job_id != '' and config_data[i]["jobID"] != job_id:
            continue
        if config_data[i]["active"] != 1:
            continue
        if config_data[i]['taskType']=='batchTouch':
            retain_sum = config_data[i]["helloSum"] - sub_task_dict[config_data[i]["jobID"]][5]
            touch_msg = json.loads(get_job_by_id(config_data[i]["jobID"])[0][6])["dynamic_job_config"]["touch_msg"]
            job_name = json.loads(query_template_config(get_job_by_id(config_data[i]["jobID"])[0][12])[0][0])["job_name"]
            r_job = {
                "jobID":config_data[i]["jobID"],
                "job_name":job_name,
                "taskType":config_data[i]['taskType'],
                "helloSum": retain_sum,
                # "timeMount":time_percent_filtered,
                "filter": config_data[i]["filter"],
                "touch_msg": touch_msg
            }
            res.append(r_job)
    return res

def get_job_by_id_service(job_id):
    return get_job_by_id(job_id)

def get_undo_task(account_id, job_id, ver):
    #取当天任务
    #根据当前时间点计算返回config的适配
    #向log表插入每个小task的记录
    config_data = json.loads(get_account_task_db(account_id))

    today_date = format_time(datetime.now(), '%Y-%m-%d')
    today_sub_task_log = get_account_task_log_db(account_id, today_date)  
    for j in config_data:
        if job_id != '' and job_id!=j["jobID"]:
            continue
        log_need_init = True
        for log in today_sub_task_log:
            if log[2] == j["jobID"]:
                log_need_init = False
        if j['taskType']=='batchTouch' and log_need_init:
            logger.info(f'get_undo_task init job {account_id}, {j["jobID"]}, {today_date}, no task log, will init')
            init_task_log_db(account_id, j["jobID"], today_date, j["helloSum"])
    today_sub_task_log = get_account_task_log_db(account_id, today_date)
    if ver == 'v1':
        res = re_org_task(config_data, today_sub_task_log, job_id)
    else:
        res = re_org_task_v2(config_data, today_sub_task_log, job_id)
    logger.info(f'get_undo_task for {account_id}, {job_id}, {today_date}, will return {res}')
    return res

def update_touch_task(account_id, job_id, hello_cnt=1):
    hello_exec_db(account_id, job_id, format_time(datetime.now(), '%Y-%m-%d'), hello_cnt)

def generate_task(jobs):
    base_config = config['task']['task_config_base']
    ret = []
    for job_id in jobs:
        item = copy.deepcopy(base_config)
        item['taskType'] = 'batchTouch'
        item['jobID'] = job_id
        ret.append(item)
    return ret


def friend_report_service(account_id, candidate_id):
    add_friend_report(account_id, candidate_id)

def get_one_time_task_service(account_id):
    db_ret = get_one_time_task_by_account_id(account_id)
    ret = []
    for d in db_ret:
        ret.append({
            "task_id": d[0],
            "task_config":json.loads(d[1])
        })
    return ret

def update_one_time_status_service(status, id):
    return update_one_time_status_by_id(status, id)

def new_one_time_task_service(account_id, one_time_task_config):
    return new_one_time_task_db(account_id, one_time_task_config)

def get_one_time_task_list_service(account_id):
    db_ret = get_one_time_task_list_db(account_id)
    ret = []
    for dr in db_ret:
        ret.append({
            "id":dr[0],
            "task_config":json.loads(dr[1]),
            "status":dr[2]
        })
    return ret