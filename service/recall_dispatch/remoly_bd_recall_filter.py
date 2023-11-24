from dao.task_dao import *
from datetime import datetime
import time


def remoly_bd_recall_filter(chat_info, flag):
    job_id = chat_info[7]
    candidate_id = chat_info[0]
    account_id = chat_info[8]
    recall_cnt = chat_info[6]

    if recall_cnt > 1:
        return False, ""

    recall_strategy_config = fetch_config(job_id)
    msgs, status_infos = fetch_candidate_infos(job_id, account_id, candidate_id)
    if msgs is None or status_infos is None:
        return False, ""

    res = fetch_msg(msgs, status_infos, recall_strategy_config)

    return True if len(res) > 0 else False, res


def fetch_candidate_infos(job_id, account_id, candidate_id):
    candidate_info = query_chat_db(account_id, job_id, candidate_id)
    source, details, contact = candidate_info

    res = query_status_infos(candidate_id, account_id)
    status_infos = None
    if len(res) > 0:
        status_infos = json.loads(res[0][0])
    return details, status_infos


def fetch_config(job_id):
    task_config = json.loads(get_job_by_id(job_id)[0][6])
    recall_strategy_config = task_config["recall_strategy_config"] if "recall_strategy_config" in task_config else None
    return recall_strategy_config


def fetch_chats(candidate_id, account_id, job_id):
    candidate_info = query_chat_db(candidate_id, account_id, job_id)
    source, details, contact = candidate_info
    return details


def has_user_reply(msgs):
    for msg in msgs:
        if msg["speaker"] == "user":
            return True

    return False


def fetch_msg(msgs, status_infos, recall_strategy_config):
    if not has_user_reply(msgs):
        res = user_not_reply_strategy(msgs, recall_strategy_config)
        return res

    return ""


def user_not_reply_strategy(msgs, recall_strategy_config):
    date = datetime.strptime(msgs[-1]["time"], "%Y-%m-%d %H:%M:%S")
    msg_time = int(date.timestamp())

    now_time = int(time.time())
    if now_time - msg_time > 86400:
        return "您好，想请问一下，最近贵公司的出海业务，有需要海外人力资源方面的服务吗?\n" \
               "我们是专注于中国企业出海的global人力资源公司，可以为你提供全世界大部分国家的EOR、payroll和recruitment的服务。"

    return ""
