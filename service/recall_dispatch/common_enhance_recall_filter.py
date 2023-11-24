from dao.task_dao import *
from datetime import datetime
import time


def common_enhance_recall_filter(chat_info, flag):
    job_id = chat_info[7]
    candidate_id = chat_info[0]
    account_id = chat_info[8]
    recall_cnt = chat_info[6]

    recall_strategy_config = fetch_config(job_id)
    msgs = fetch_candidate_infos(job_id, account_id, candidate_id)
    if msgs is None:
        return False, ""

    msg = fetch_msg(msgs, recall_cnt, recall_strategy_config)

    return True if len(msg) > 0 else False, msg


def has_user_reply(msgs):
    for msg in msgs:
        if msg["speaker"] == "user":
            return True

    return False


def fetch_msg(msgs, recall_cnt, config):
    if has_user_reply(msgs) and config["reply_filter_flag"]:
        return ""

    index = recall_cnt + 1
    recall_msg_info_list = config["recall_msg_info_list"]

    if index >= len(recall_msg_info_list):
        return

    date = datetime.strptime(msgs[-1]["time"], "%Y-%m-%d %H:%M:%S")
    msg_time = int(date.timestamp())
    now_time = int(time.time())
    if now_time - msg_time > recall_msg_info_list[index]["threshold"]:
        return recall_msg_info_list[index]["msg"]


def fetch_config(job_id):
    task_config = json.loads(get_job_by_id(job_id)[0][6])
    recall_strategy_config = task_config["recall_strategy_config"] if "recall_strategy_config" in task_config else None
    return recall_strategy_config


def fetch_candidate_infos(job_id, account_id, candidate_id):
    candidate_info = query_chat_db(candidate_id, account_id, job_id)
    source, details, contact = candidate_info

    return details
