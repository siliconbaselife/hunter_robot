from dao.task_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime


# def convert_to_int(time_percent):



def filter_time(time_percent, retain_sum):
    sum = 0
    filter_time_res = []
    t_now = time.strftime("%H:%M", time.localtime())
    for t in time_percent:
        if t["time"] > t_now:
            filter_time_res.append(t)
            sum += t["mount"]
    for t in filter_time_res:
        t["mount"] = round(t["mount"] / sum * retain_sum) 
    return filter_time_res


## 处理重启后的任务的适配
def re_org_task(config_data, today_sub_task_log):
    sub_task_dict = {}
    for t in today_sub_task_log:
        sub_task_dict[t[2]] = t
    res = []
    for job_config in config_data:
        if job_config['taskType']=='batchTouch':
            retain_sum = job_config["helloSum"] - sub_task_dict[job_config["jobID"]][5]

            time_percent = job_config["timeMount"]
            time_percent_filtered = filter_time(time_percent, retain_sum)

            r_job = {
                "jobID":job_config["jobID"],
                "taskType":job_config['taskType'],
                "helloSum": retain_sum,
                "timeMount":time_percent_filtered
            }
            res.append(r_job)
    return res



def get_undo_task(account_id):
    #取当天任务
    #根据当前时间点计算返回config的适配
    #向log表插入每个小task的记录
    config_data = json.loads(get_account_task_db(account_id))

    today_date = format_time(datetime.now(), '%Y-%m-%d')
    today_sub_task_log = get_sub_task_with_account_id_db(account_id, today_date)
    if len(today_sub_task_log)== 0:
        for j in config_data:
            if j['taskType']=='batchTouch':
                init_task_log_db(account_id, j["jobID"], today_date, j["helloSum"])
        return config_data
    else:
        return re_org_task(config_data, today_sub_task_log)


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

