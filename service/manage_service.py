from dao.task_dao import *
import json
import time
from utils.config import config
from utils.utils import format_time
import copy
from datetime import datetime


def candidate_list_service(job_id, start, limit):
    chat_list = get_chats_by_job_id(job_id, start, limit)
    res_chat_list = []
    for chat in chat_list:
        candidate_info = query_candidate_by_id(chat[2])
        if len(candidate_info) == 0:
            candidate_info_detail = {}
        else:
            candidate_info_detail = candidate_info[0]
        res_chat = {
            "candidate_id": chat[2],
            "candidate_name": chat[3],
            "source":chat[4],
            "contact":chat[6],
            "details":chat[7],
            "candidate_info_detail": candidate_info_detail[7],
            "update_time":chat[10].strftime("%Y-%m-%d %H:%M:%S")
        }
        res_chat_list.append(res_chat)
    
    chat_sum = get_chats_num_by_job_id(job_id)[0][0]
    return chat_sum, res_chat_list


