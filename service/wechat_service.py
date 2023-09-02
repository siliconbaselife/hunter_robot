from dao.wechat_dao import *
from dao.task_dao import *
import json
import random

def own_msg_report(wechat_account_id, wechat_alias_id, msg_send):
    f_info = get_chat_by_alias_id(wechat_alias_id, wechat_account_id)
    if f_info[6] != 2:
        logger.info(f"own_msg_report_error, user status wrong, {wechat_alias_id}, {wechat_account_id}, {msg_send}")
        return
    detail = json.load(f_info[5])
    msg = {
        "role": "robot",
        "msg": msg_send
    }
    detail.append(msg)
    update_detail(wechat_alias_id, wechat_account_id, json.dumps(detail, ensure_ascii=False))
    

def user_msg_report(wechat_account_id, wechat_alias_id, msg_receive):
    f_info = get_chat_by_alias_id(wechat_alias_id, wechat_account_id)
    if f_info[6] != 2:
        friend_status_update_by_alias_id(wechat_account_id, wechat_alias_id, 2)
        detail = []
    else:
        detail = json.load(f_info[5])        
    msg = {
        "role": "user",
        "msg": msg_receive
    }
    detail.append(msg)
    update_detail(wechat_alias_id, wechat_account_id, json.dumps(detail, ensure_ascii=False))


def friend_report(wechat_account_id, wechat_alias_id, wechat_id):
    #添加好友的动作上报，这时对方尚未同意，对方同意那一刻有消息回溯，会在第一条消息再更新状态
    friend_status_update_by_id(wechat_account_id, wechat_id, 1)

def new_wechat_chat_service(candidate_id, candidate_name, wechat_account_id, wechat_id,wechat_alias_id,  hello_msg):
    
    detail = [{
        "role" : "robot",
        "msg" : hello_msg
    }]
    ##尚未发送请求，需要report的时候再修改状态
    status = 0
    new_wechat_chat_db(candidate_id, candidate_name, wechat_id, wechat_alias_id, wechat_account_id, detail, status)


def _get_add_friend_task(account_info):
    ##先写一个简单策略
    task_res = []
    wechat_account_id = account_info[0]
    task_config = json.loads(account_info[1])
    job_config = task_config['job_config']
    for job_c in job_config:
        job_id = job_c['job_id']
        job_info = get_job_by_id(job_id)[0]
        hello_msg = job_c['hello_msg'].format(job_info[1])
        candidate_list = get_candidate_update_last_hour(job_id)
        for candidate in  candidate_list:
            candidate_id = candidate[1]
            candidate_name = candidate[2]
            contact_info = json.loads(candidate[3])
            wechat_id = contact_info['wechat']
            if wechat_id == "" or wechat_id == None or wechat_id == "None" or wechat_id == "NULL":
                continue
            if candidate_already_friend(candidate_id):
                continue
            wechat_alias_id = candidate_name + "-" + candidate_id
            new_wechat_chat_service(candidate_id, candidate_name, wechat_account_id, wechat_id, wechat_alias_id, hello_msg)
            task_res.append({
                "alias_id": wechat_alias_id,
                "msg": hello_msg
            })
    return {
        "task_type":"add_friend",
        "content": task_res
    }


def _get_send_msg_task(account_info):
    return {
        "task_type":"send_msg",
        "content": []
    }


def task_to_do(wechat_account_id):
    account_info = get_wechat_account_info(wechat_account_id)

    task_list = [
        _get_add_friend_task(account_info),
        _get_send_msg_task(account_info)
    ]
    return task_list