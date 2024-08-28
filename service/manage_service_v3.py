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

logger = get_logger(config['log']['log_file'])

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
        ret_job = new_job_service_v3(manage_account_id, platform, job_config, template_config, job_id, platform_id)
    else:
        ret_job = update_dynamic_job_conifg_v3(job_config)

    ret_task = update_task_config_service_v3(manage_account_id, account_id, task_config, job_config)
    logger.info(f"update_config_service_v3: ret_temp {ret_temp}, ret_job {ret_job}, ret_task {ret_task}")



def update_dynamic_job_conifg_v3(dynamic_job_config):
    job_config_json = get_job_by_id(dynamic_job_config['job_id'])[0][6]
    job_config = json.loads(job_config_json)
    dynamic_job_config['touch_msg'] = process_str(dynamic_job_config['touch_msg'])
    dynamic_job_config['recall_msg_list'] = [process_str(recall_msg).replace('"', "")
        .replace("'","")
        .replace("\n", ";")
        .replace('\"', "")
        .replace("\'", "") for recall_msg in dynamic_job_config['recall_msg_list']]

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
                "threshold": 86400*(i+1),
                "msg": recall_msg.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            }
        for i, recall_msg in enumerate(dynamic_job_config['recall_msg_list'])],
        "reply_filter_flag": True
    }
    job_config_json = json.dumps(job_config, ensure_ascii=False)
    logger.info(f'update_dynamic_job_conifg_v3: {dynamic_job_config["job_id"]}, {job_config_json}')
    return only_update_job_conifg_db(dynamic_job_config['job_id'], job_config_json)


def new_job_service_v3(manage_account_id, platform_type, dynamic_job_config, template_config, job_id, platform_id):
    # 自定义筛选，后续这个再处理
    custom_filter = 0
    # 账号共享
    share = 0
    dynamic_job_config['touch_msg'] = process_str(dynamic_job_config['touch_msg']) \
        .replace('"', "") \
        .replace("'","") \
        .replace("\n", ";") \
        .replace('\"', "") \
        .replace("\'", "")

    dynamic_job_config['recall_msg_list'] = [process_str(recall_msg).replace('"', "")
        .replace("'","")
        .replace("\n", ";")
        .replace('\"', "")
        .replace("\'", "") for recall_msg in dynamic_job_config['recall_msg_list']]
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
        logger.info(f"new_job_service_v3, use chat_config_v3: {job_config['chat_config']}")
    except:
        job_config['chat_config'] = config['job_register'][platform_type]["chat_config_v2"]
        logger.info(f"new_job_service_v3, use chat_config_v3 failed: use chat_config_v2: {job_config['chat_config']}")

    job_config['recall_config_filter'] = "common_enhance_recall_filter"
    job_config['recall_strategy_config'] = {
        "recall_msg_info_list": [
            {
                "threshold": 86400*(i+1),
                "msg": recall_msg.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            }
        for i, recall_msg in enumerate(dynamic_job_config['recall_msg_list'])],
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
    logger.info(f'new_job_service_v3: {platform_type} {platform_id} {job_name} {robot_api} {job_config_json}, {share}, {manage_account_id},{robot_template}')
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

def chat_list_service(job_id, begin_time, end_time, page, limit, with_phone, with_wechat, with_reply, with_resume):
    return_list = []
    candidate_list = chat_parse(job_id, begin_time, end_time, page, limit, with_phone, with_wechat, with_reply, with_resume)
    for item in candidate_list:
        cid = item['id']
        flag, detail = query_candidate_detail(cid)
        gender, degree, school, age=None, None, None, None
        if not flag:
            logger.warning(f"chat_list_service, job {job_id} candidate {cid} no details, will skip")
            continue
        gender = '男' if detail['geekCard']['geekGender']==1 else '女'
        degree = detail['geekCard']['geekDegree']
        school = detail['geekCard']['geekEdu']['school']
        age = detail['geekCard']['ageDesc'].replace('岁', '')
        item['age'] = age
        item['gender'] = gender
        item['degree'] = degree
        item['school'] = school
        return_list.append(item)
    return return_list

def stat_chat_service(job_id, begin_time, end_time, page, limit, with_phone, with_wechat, with_reply, with_resume):
    user_ask_cv_cnt = 0
    user_ask_cnt = 0
    with_cv_cnt = 0
    hello_cnt = 0
    reply_cnt = 0
    with_phone_cnt = 0
    with_wechat_cnt = 0
    candidate_list = chat_parse(job_id, begin_time, end_time, page, limit, with_phone, with_wechat, with_reply, with_resume)

    for item in candidate_list:
        source, cv, phone, wechat, user_reply, chat_info_list = item['source'], item['cv'], item['phone'], item['wechat'], item['reply'], item['chat']
        if cv is not None:
            with_cv_cnt+=1
        if phone is not None:
            with_phone_cnt+=1
        if wechat is not None:
            with_wechat_cnt+=1

        if source=='user_ask':
            user_ask_cnt+=1
            if cv is not None:
                user_ask_cv_cnt+=1
        else:
            hello_cnt+=1
        
        if user_reply:
            reply_cnt+=1
            
    reply_ratio = reply_cnt/ hello_cnt if hello_cnt!=0 else 0
    return {
        'user_ask_cv_cnt': user_ask_cv_cnt,
        'user_ask_cnt': user_ask_cnt,
        'with_cv_cnt': with_cv_cnt,
        'hello_cnt': hello_cnt,
        'reply_cnt': reply_cnt,
        'reply_ratio': reply_ratio,
        'with_phone_cnt': with_phone_cnt,
        'with_wechat_cnt': with_wechat_cnt
    }


def job_list_service(manage_account_id):
    ret_list = []
    for item in get_job_info_by_account(manage_account_id):
        ret_list.append({
            'jobId': item[0],
            'jobName': item[1]        
        })

def chat_parse(job_id, begin_time, end_time, page=None, limit=None, with_phone=False, with_wechat=False, with_reply=False, with_resume=False):
    chat_list = get_job_chat_db(job_id, begin_time, end_time, page, limit)

    candidate_list = []
    for cid, cname, source, status, contact, details, recall_cnt, filter_result in chat_list:
        phone, wechat, cv, user_reply, chat_info_list = None, None, None, False, []
        try:
            contact = json.loads(contact)
            phone = contact['phone']
            wechat = contact['wechat']
            cv = contact['cv']
        except BaseException as e:
            logger.info("chat_parse, error parse contact: {contact}")

        try:
            chat_info_list = json.loads(details)
            for item in chat_info_list:
                if item['speaker']=='user':
                    user_reply = True
                    break
        except BaseException as e:
            logger.info("chat_parse, error parse details: {details}")
        
        if with_phone and phone is None:
            continue
        if with_resume and cv is None:
            continue
        if with_reply and not user_reply:
            continue
        if with_wechat and wechat is None:
            continue

        candidate_list.append({
            'id': cid,
            'name': cname,
            'phone': phone,
            'wechat': wechat,
            'cv': cv,
            'reply': user_reply,
            'chat': chat_info_list,
            'source': source
        })
    return candidate_list

