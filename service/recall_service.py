from dao.task_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime
from .recall_dispatch import *



__recall_filter = {
    'common_need_recall_filter': common_need_recall_filter
}


def need_recall(chat_info, flag):
    ## 要按不同账号取
    con = 'common_need_recall_filter'

    return __recall_filter[con](chat_info, flag)


def recall_msg(account_id, candidate_ids, candidate_ids_read):
    candidate_ids_p = list(set(candidate_ids).difference(set(candidate_ids_read)))

    ##获得所有chat信息
    chat_infos_read = get_chats_by_ids(account_id, candidate_ids_read)
    chat_infos = get_chats_by_ids(account_id, candidate_ids_p)
    chat_res = []

    for chat_info in chat_infos_read:
        flag, res = need_recall(chat_info, True)
        if flag:
            chat_res.append(res)

    for chat_info in chat_infos:
        flag, res = need_recall(chat_info, False)
        if flag:
            chat_res.append(res)
    return chat_res



def recall_result(account_id, candidate_id):
    return add_recall_count(account_id, candidate_id)
    
