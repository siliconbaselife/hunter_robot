from dao.task_dao import *
import json
import time
from utils.config import config
import copy

def filter_time(time_percent):
    sum = 0
    filter_time_res = []
    t_now = time.strftime("%M:%S", time.localtime())
    for t in time_percent:
        if t["time"] > t_now:
            filter_time_res.append(t)
            sum += t["percent"]
    for t in filter_time_res:
        t["percent"] = round(t["percent"] / sum)
    return filter_time_res


## 处理重启后的任务的适配
def re_org_task(config_data, today_sub_task_log):
    sub_task_dict = {}
    for t in today_sub_task_log:
        sub_task_dict[t[2]] = t
    res = []
    for job_config in config_data:
        retain_sum = job_config["hello_sum"] - sub_task_dict[job_config["job_id"]][5]

        time_percent = job_config["time_percent"]
        time_percent_filtered = filter_time(time_percent)

        r_job = {
            "job_id":job_config["job_id"],
            "hello_sum": retain_sum,
            "time_percent":time_percent_filtered
        }
        res.append(r_job)
    return res



def get_undo_task(account_id):
    #取当天任务
    #根据当前时间点计算返回config的适配
    #向log表插入每个小task的记录
    config_data = json.loads(get_task_db(account_id)[0][2])

    today_date = ""
    today_sub_task_log = get_sub_task_with_account_id_db(account_id, today_date)
    if len(today_sub_task_log == 0):
        for j in config_data:
            init_task_log_db(account_id, j["job_id"], today_date, j["hello_sum"])
        return config_data
    else:
        return re_org_task(config_data, today_sub_task_log)


def generate_task(jobs):
    base_config = config['task_config_base']
    ret = []
    for job_id in jobs:
        item = copy.deepcopy(base_config)
        item['job_id'] = job_id
        ret.append(item)
    return ret

