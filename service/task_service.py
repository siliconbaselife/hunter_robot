from dao.task_dao import *
import json



## 处理重启的适配
def re_org_task(config_data, today_sub_task_log):
    res = []
    for job_config in config_data:
        r_job = {
            "job_id":job_config["job_id"]
        }
    return



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



def report_result():
    #
    return


