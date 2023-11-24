from dao.task_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime
from .recall_dispatch import *

__recall_filter = {
    'common_need_recall_filter': common_need_recall_filter,
    'common_enhance_recall_filter': common_enhance_recall_filter
}


def need_recall(chat_info, flag):
    job_id = chat_info[7]
    task_config = json.loads(get_job_by_id(job_id)[0][6])
    if "recall_config_filter" in task_config:
        con = task_config["recall_config_filter"]
    else:
        con = 'common_need_recall_filter'

    return __recall_filter[con](chat_info, flag)


def recall_msg(account_id, candidate_ids, candidate_ids_read):
    candidate_ids_p = list(set(candidate_ids).difference(set(candidate_ids_read)))

    ##获得所有chat信息
    chat_infos_read = get_chats_by_ids(account_id, candidate_ids_read)
    chat_infos = get_chats_by_ids(account_id, candidate_ids_p)
    chat_res = []

    for chat_info in chat_infos_read:
        chat_info.append(account_id)
        flag, res = need_recall(chat_info, True)
        if flag:
            chat_res.append(res)

    for chat_info in chat_infos:
        chat_info.append(account_id)
        flag, res = need_recall(chat_info, False)
        if flag:
            chat_res.append(res)
    return chat_res


def recall_result(account_id, candidate_id):
    return add_recall_count(account_id, candidate_id)
