from utils.config import config
from utils.log import  get_logger
from dao.task_dao import query_account_type_db
from .chat_dispatch import *
from dao.task_dao import *

logger = get_logger(config['log']['log_file'])
__chat_dispatcher = {
    'base_common_chat': BaseChatRobot,
    'maimai_common_chat': MaimaiRobot,
    'maimai_simple_chat': MaimaiSimpleRobot
}

def chat_service(account_id, job_id, candidate_id, robot_api, page_history_msg, db_history_msg, source):
    job_res = get_job_by_id(job_id)
    if len(job_res) == 0:
        logger.info(f"chat_service: job config wrong, not exist: {job_id}, {candidate_info['id']}")
    chat_key = json.loads(job_res[0][6],strict=False)["chat_config"]
    assert chat_key in __chat_dispatcher, f"chat_service: unsupport job chat key {chat_key} from account {account_id}"
    Robot = __chat_dispatcher[chat_key]
    robot = Robot(robot_api, account_id, job_id, candidate_id, source=source)
    robot.contact(page_history_msg=page_history_msg, db_history_msg=db_history_msg)
    return {
        'next_step': robot.next_step,
        'next_msg': robot.next_msg,
        'msg_list': robot.msg_list,
        'source': robot.source,
        'status': robot.status
    }
