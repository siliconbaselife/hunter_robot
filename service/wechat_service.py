from dao.wechat_dao import *
import json

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


def _get_add_friend_task(account_info):
    ##先写一个简单策略
    task_config = json.loads(account_info[1])
    job_config = task_config['job_config']
    for job_c in job_config:
        job_id = job_c['job_id']
        

    return {
        "task_type":"add_friend",
        "content": []
    }


def _get_send_msg_task(account_info):
    return {
        "task_type":"send_msg",
        "content": []
    }


def task_to_do(wechat_account_id):
    account_info = get_wechat_account_info(wechat_account_id)
    



    task_list = [
        _get_add_friend_task(wechat_account_id),
        _get_send_msg_task(wechat_account_id)
    ]
    return task_list