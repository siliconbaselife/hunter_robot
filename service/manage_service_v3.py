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

def update_config_service_v3(manage_account_id, account_id, platform, params):
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

    ret_task = update_task_config_service_v3(manage_account_id, account_id, task_config, job_config)
    logger.info(f"update_config_service_v3: ret_temp {ret_temp}, ret_job {ret_job}, ret_task {ret_task}")



def update_dynamic_job_conifg(dynamic_job_config):
    job_config_json = get_job_by_id(dynamic_job_config['job_id'])[0][6]
    job_config = json.loads(job_config_json)
    dynamic_job_config['touch_msg'] = process_str(dynamic_job_config['touch_msg'])
    dynamic_job_config['recall_msg'] = process_str(dynamic_job_config['recall_msg'])

    if 'filter_config' in dynamic_job_config:
        update_filter_config = dynamic_job_config.pop('filter_config')
        job_config['filter_config'] = update_filter_config
    if 'chat_config' in dynamic_job_config:
        update_chat_config = dynamic_job_config.pop('chat_config')
        job_config['chat_config'] = update_chat_config
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
        job_config['filter_config'] = config['job_register'][platform_type]["filter_config_v3"]
    else:
        job_config['filter_config'] = config['job_register'][platform_type]["custom_filter_config"]
    try:
        job_config['chat_config'] = config['job_register'][platform_type]["chat_config_v3"]
        logger.info(f"new_job_service, use chat_config_v3: {job_config['chat_config']}")
    except:
        job_config['chat_config'] = config['job_register'][platform_type]["chat_config_v3"]
        logger.info(f"new_job_service, use chat_config_v3: {job_config['chat_config']}")

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


def update_task_config_service_v3(manage_account_id, account_id, filter_task_config, job_config):
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
