from utils.config import config
from utils.log import  get_logger
from dao.task_dao import query_account_type_db
from .chat_dispatch import *

logger = get_logger(config['log']['log_file'])
__chat_dispatcher = {
    'Boss': BaseChatRobot,
    'Linkedin': BaseChatRobot,
    'maimai': MaimaiRobot
}

def chat_service(account_id, job_id, candidate_id, robot_api, page_history_msg, db_history_msg, source):
    platform_type = query_account_type_db(account_id)
    
    assert platform_type in __chat_dispatcher, f"chat_service: unsupport platform type {platform_type} from account {account_id}"
    Robot = __chat_dispatcher[platform_type]
    robot = Robot(robot_api, account_id, job_id, candidate_id, source=source)
    robot.contact(page_history_msg=page_history_msg, db_history_msg=db_history_msg)
    return {
        'next_step': robot.next_step,
        'next_msg': robot.next_msg,
        'msg_list': robot.msg_list,
        'source': robot.source,
        'status': robot.status
    }
