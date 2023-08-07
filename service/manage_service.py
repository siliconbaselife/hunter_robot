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
        res_chat = {
            "candidate_id": chat[2],
            "candidate_name": chat[3],
            "source":chat[4],
            "contact":chat[5],
            "details":chat[6]
        }
        res_chat_list.append(res_chat)
    return res_chat_list



