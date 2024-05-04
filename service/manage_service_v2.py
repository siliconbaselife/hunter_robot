from dao.task_dao import *
from dao.manage_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time, process_list, process_str, process_str_to_list, str_is_none, generate_random_digits
import copy
from datetime import datetime
from pymysql.converters import escape_string
from service.manage_service import delete_task, get_manage_config_service, template_insert_service, \
    template_update_service


def check_limit(manage_account_id):
    account_num = len(my_account_list_db_v2(manage_account_id, 'v2'))
    max_account_num = get_account_nums_db(manage_account_id)
    return int(account_num) >= int(max_account_num)


def delete_account(manage_account_id, account_id, job_ids, template_ids):
    delete_account_db(account_id, manage_account_id)
    for j in job_ids:
        delete_job_db(j)
    for t in template_ids:
        delete_template_db(t)


def delete_config_v2(manage_account_id, account_id, job_id, template_id):
    delete_task(manage_account_id, account_id, job_id)
    delete_job_db(job_id)
    delete_template_db(template_id)


def my_account_list_service_v2(manage_account_id):
    accounts_db = my_account_list_db_v2(manage_account_id, 'v2')
    ret_list = []
    for a_d in accounts_db:
        jobs = json.loads(a_d[3])
        jobs_ret = {}
        llm_ret = {}
        for job_id in jobs:
            job_db = get_job_by_id(job_id)[0]
            job_config = json.loads(job_db[6])['dynamic_job_config']
            llm_config = json.loads(get_llm_config_by_id_db(job_db[12]))
            jobs_ret[job_db[0]] = job_config
            llm_ret[job_db[0]] = llm_config

        task_configs = json.loads(a_d[4])
        param_ret = []
        for t in task_configs:
            param_ret.append({
                "template_config": llm_ret[t['jobID']],
                "job_config": jobs_ret[t['jobID']],
                "task_config": t['filter'],
                "active": t['active']
            })
        account = {
            "account_id": a_d[0],
            "platform": a_d[1],
            "account_name": a_d[2],
            "config": param_ret
        }
        ret_list.append(account)
    return ret_list


def update_dynamic_job_conifg(dynamic_job_config):
    job_config_json = get_job_by_id(dynamic_job_config['job_id'])[0][6]
    job_config = json.loads(job_config_json)
    dynamic_job_config['touch_msg'] = process_str(dynamic_job_config['touch_msg'])
    dynamic_job_config['recall_msg'] = process_str(dynamic_job_config['recall_msg'])
    job_config['dynamic_job_config'] = dynamic_job_config
    job_config['recall_strategy_config'] = {
        "recall_msg_info_list": [
            {
                "threshold": 86400,
                "msg": dynamic_job_config['recall_msg']
            }
        ],
        "reply_filter_flag": True
    }
    return only_update_job_conifg_db(dynamic_job_config['job_id'], json.dumps(job_config, ensure_ascii=False))


def new_job_service(manage_account_id, platform_type, dynamic_job_config, template_config, job_id, platform_id):
    # 自定义筛选，后续这个再处理
    custom_filter = 0
    # 账号共享
    share = 0
    dynamic_job_config['touch_msg'] = process_str(dynamic_job_config['touch_msg']).replace('"', "").replace("'",
                                                                                                            "").replace(
        "\n", ";").replace('\"', "").replace("\'", "")
    dynamic_job_config['recall_msg'] = process_str(dynamic_job_config['recall_msg']).replace('"', "").replace("'",
                                                                                                              "").replace(
        "\n", ";").replace('\"', "").replace("\'", "")
    job_config = {}
    job_config['jobID'] = job_id
    job_config['custom_filter'] = custom_filter
    job_config['custom_filter_content'] = ""
    if custom_filter == 0:
        job_config['filter_config'] = config['job_register'][platform_type]["filter_config_v2"]
    else:
        job_config['filter_config'] = config['job_register'][platform_type]["custom_filter_config"]
    job_config['chat_config'] = config['job_register'][platform_type]["chat_config_v2"]
    job_config['recall_config_filter'] = "common_enhance_recall_filter"
    job_config['recall_strategy_config'] = {
        "recall_msg_info_list": [
            {
                "threshold": 86400,
                "msg": dynamic_job_config['recall_msg'].replace('"', "").replace("'", "").replace("\n", ";").replace(
                    '\"', "").replace("\'", "")
            }
        ],
        "reply_filter_flag": True
    }

    manage_config = json.loads(get_manage_config_service(manage_account_id))
    job_config['group_msg'] = manage_config['group_msg']
    job_config['dynamic_job_config'] = dynamic_job_config

    robot_template = template_config["template_id"]
    job_name = dynamic_job_config["job_name"]
    robot_api = '/vision/chat/receive/message/chat/v1'
    # 废字段
    jd = ''

    job_config_json = json.dumps(job_config, ensure_ascii=False)
    logger.info(
        f'new_job_service: {platform_type} {platform_id} {job_name} {robot_api} {job_config_json}, {share}, {manage_account_id},{robot_template}')
    return register_job_db(job_id, platform_type, platform_id, job_name, jd, robot_api, job_config_json, share,
                           manage_account_id, robot_template)


def update_config_service_v2(manage_account_id, account_id, platform, params):
    template_config = params['template_config']
    job_config = params['job_config']
    task_config = params['task_config']
    template_config['work_location'] = ",".join(task_config['location'])

    if str_is_none(template_config.get('template_id', '')):
        template_name = job_config['job_name']
        template_id = template_name + "_" + str(int(time.time()))
        template_config['template_id'] = template_id
        template_config['template_name'] = template_name
        ret_temp = template_insert_service(manage_account_id, template_id, template_name, template_config)
    else:
        ret_temp = template_update_service(manage_account_id, template_config['template_id'],
                                           template_config['template_name'], template_config)

    if str_is_none(job_config.get('job_id', '')):
        platform_id = str(generate_random_digits(10))
        job_id = f'job_{platform}_{platform_id}'
        job_config['job_id'] = job_id
        ret_job = new_job_service(manage_account_id, platform, job_config, template_config, job_id, platform_id)
    else:
        ret_job = update_dynamic_job_conifg(job_config)

    ret_task = update_task_config_service_v2(manage_account_id, account_id, task_config, job_config)
    logger.info(f"update_config_service_v2: ret_temp {ret_temp}, ret_job {ret_job}, ret_task {ret_task}")


def update_task_config_service_v2(manage_account_id, account_id, filter_task_config, job_config):
    task_config = {
        "jobID": job_config['job_id'],
        "helloSum": filter_task_config['hello_sum'],
        "taskType": "batchTouch",
        "timeMount": [{
            "time": "09:00",
            "mount": filter_task_config['hello_sum']
        }],
        "filter": filter_task_config,
        "active": 1
    }

    task_configs = json.loads(get_account_task_db(account_id))
    flag = True
    for i in range(0, len(task_configs)):
        if task_configs[i]["taskType"] == "batchTouch" and task_configs[i]["jobID"] == task_config["jobID"]:
            task_configs[i] = task_config
            flag = False
    if flag:
        task_configs.append(task_config)

    job_list = []
    for t in task_configs:
        job_list.append(t['jobID'])

    return account_config_update_db(manage_account_id, account_id, json.dumps(task_configs, ensure_ascii=False),
                                    json.dumps(job_list, ensure_ascii=False))


def update_task_active(manage_account_id, account_id, job_id, active):
    task_configs = json.loads(get_account_task_db(account_id))
    jobs = get_account_jobs_db(account_id)
    for i in range(0, len(task_configs)):
        if task_configs[i]["jobID"] == job_id:
            task_configs[i]["active"] = active
            break
    return account_config_update_db(manage_account_id, account_id, json.dumps(task_configs, ensure_ascii=False), jobs)


def query_myjob_lists(manage_account_id, account_id):
    config_raw = select_extention_config(manage_account_id, account_id)
    if config_raw is None:
        return []

    config = json.loads(config_raw)
    if "jobnames" not in config:
        return []

    return config["jobnames"]


def update_myjob_lists(manage_account_id, account_id, jobnames):
    config_raw = select_extention_config(manage_account_id, account_id)
    if config_raw is None:
        config = {}
    else:
        config = json.loads(config_raw)

    config["jobnames"] = jobnames
    update_extention_config(manage_account_id, account_id, config)
