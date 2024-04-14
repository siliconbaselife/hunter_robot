from dao.chat_dao import query_conf, add_conf, update_conf, query_confs, query_chat, add_chat, update_chat
from dao.tool_dao import query_profile_tag_relation_by_user_and_candidate_db

from utils.log import get_logger
from utils.config import config as config
from algo.llm_inference import gpt_manager

import time

logger = get_logger(config['log']['log_file'])


def conf(user_id, tag, conf):
    data_conf = query_conf(user_id, tag)
    if data_conf is not None:
        update_conf(user_id, tag, conf)
    add_conf(user_id, tag, conf)


def get_conf(user_id):
    return query_confs(user_id)


def has_say(details):
    if len(details) > 1:
        return True

    if len(details) == 0:
        return False

    if details[0]["speaker"] == "robot":
        return False

    return True


def has_reply(details):
    if len(details) == 0:
        return False

    if details[-1]["speaker"] == "robot":
        return False

    flag = False
    num = 0
    for i in range(len(details)):
        index = len(details) - 1 - i
        msg_info = details[index]
        if msg_info["speaker"] == "robot":
            now_flag = False
        else:
            now_flag = True

        if not flag and now_flag:
            num += 1
        flag = now_flag

    return num == 1


def is_positive_negtive(details, tag_conf):
    msgs = ""
    for detail in details:
        if detail["speaker"] == "robot":
            msgs += "me:" + detail["msg"] + "/n"
        else:
            msgs += "candidate:" + detail["msg"] + "/n"

    prompt = f'''
You're a headhunter, can you help me determine whether the candidate is interested in the opportunity or not based on the following conversation?
+++
{msgs}
+++
A. Interested in the opportunity B. Not interested in the opportunity C.Can't tell   
'''

    result_msg = gpt_manager.chat_task(prompt)

    if "B.Not interested in the opportunity" in result_msg:
        return False
    else:
        return True


def chat_to_candidate(details, tag_conf):
    need_reply = has_reply(details)
    if not need_reply:
        return [{"action": "no_talk", "msg": ""}]
    f = is_positive_negtive(details, tag_conf)
    return tag_conf["positive"] if f else tag_conf["negtive"]


def recall_to_candidate(details, tag_conf):
    msg = tag_conf["msg"]
    if msg is None or len(msg) == 0:
        return [{"action": "no_talk", "msg": ""}]

    last_time = details[-1]["time"]
    now_time = time.time()
    if now_time - last_time > 24 * 60 * 60:
        return [{"action": "say", "msg": msg}]
    return [{"action": "no_talk", "msg": ""}]


def fetch_candidate_tag(user_id, candidate_id):
    data = query_profile_tag_relation_by_user_and_candidate_db(user_id, candidate_id, "Linkedin")
    if len(data) == 0:
        return None
    return data[0][1]


def chat(user_id, account_id, candidate_id, details):
    tag = fetch_candidate_tag(user_id, candidate_id)
    logger.info(f"user_id chat tag: {tag}")
    if tag is None:
        return [{"action": "no_talk", "msg": ""}]
    tag_conf = query_conf(user_id, tag)
    logger.info(f"user_id chat tag_conf: {tag_conf}")

    say_flag = has_say(details)
    logger.info(f"user_id chat say_flag: {say_flag}")
    if say_flag:
        msg_infos = chat_to_candidate(details, tag_conf)
    else:
        msg_infos = recall_to_candidate(details, tag_conf)
    logger.info(f"user_id chat msg_infos: {msg_infos}")

    if len(msg_infos) == 0:
        return msg_infos

    details.extends(msg_infos)
    history_chat = query_chat(user_id, account_id, candidate_id)
    if history_chat is not None:
        update_chat(user_id, account_id, candidate_id, details)
    else:
        add_chat(user_id, account_id, candidate_id, details)

    return msg_infos
