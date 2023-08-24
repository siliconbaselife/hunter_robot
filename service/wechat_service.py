from dao.wechat_dao import *
import json

def own_msg_report(wechat_account_id, wechat_alias_id, msg_send):
    f_info = get_chat_by_wechat_id(wechat_alias_id, wechat_account_id)
    if f_info[6] != 2:
        logger.info(f"own_msg_report_error, user status wrong, {wechat_alias_id}, {wechat_account_id}")
        return
    detail = json.load(f_info[5])
    msg = {
        "role": "robot",
        "msg": msg_send
    }
    detail.append(msg)
    

def user_msg_report():
    
    return


def friend_report(wechat_account_id, wechat_alias_id, wechat_id):
    #添加好友的动作上报，这时对方尚未同意，对方同意那一刻有消息回溯，会在第一条消息再更新状态
    friend_status_update(wechat_account_id, wechat_id, 1)

def task_to_do():
    return