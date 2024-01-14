from dao.task_dao import *
from datetime import datetime
import time


def common_enhance_recall_filter(chat_info, flag):
    job_id = chat_info[7]
    candidate_id = chat_info[0]
    account_id = chat_info[8]
    recall_cnt = chat_info[6]
    candidate_name = chat_info[1]

    recall_strategy_config = fetch_config(job_id)
    msgs = fetch_candidate_infos(job_id, account_id, candidate_id)
    
    if msgs is None:
        return False, ""

    msg = fetch_msg(msgs, recall_cnt, recall_strategy_config)

    return True if len(msg) > 0 else False, {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "job_id": job_id,
            "need_recall": True,
            "recall_msg": msg
        }


def has_user_reply(msgs):
    for msg in msgs:
        if msg["speaker"] == "user":
            return True

    return False


def fetch_msg(msgs, recall_cnt, config):
    if has_user_reply(msgs) and config["reply_filter_flag"]:
        return ""

    index = recall_cnt
    recall_msg_info_list = config["recall_msg_info_list"]

    if index >= len(recall_msg_info_list):
        return ""

    date = datetime.strptime(str(msgs[-1]["time"]), "%Y-%m-%d %H:%M:%S")
    msg_time = int(date.timestamp())
    now_time = int(time.time())
    if now_time - msg_time > recall_msg_info_list[index]["threshold"]:
        return recall_msg_info_list[index]["msg"]

    return ""


def fetch_config(job_id):
    task_config = json.loads(get_job_by_id(job_id)[0][6])
    recall_strategy_config = task_config["recall_strategy_config"] if "recall_strategy_config" in task_config else None
    return recall_strategy_config


def fetch_candidate_infos(job_id, account_id, candidate_id):
    try:
        candidate_info = query_chat_db(account_id, job_id, candidate_id)
        if len(candidate_info) == 0:
            return None

        details = candidate_info[0][1]
        return json.loads(details)
    except BaseException as e:
        logger.info(f'common_enhance_recall_filter_msg,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')
        logger.info(f'common_enhance_recall_filter_msg,{details}')
        return None