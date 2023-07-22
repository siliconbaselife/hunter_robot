import requests
from datetime import datetime
from utils import format_time
from config import config
from logger import get_logger

logger = get_logger(config['log_file'])

def chat_contact(robot_api, sess_id, last_msg):
    data = {
        "conversation_id": sess_id, # 对话id
        "message": last_msg, # 消息内容
        "message_time": format_time(datetime.now())
    }
    url = config['chat']['chat_url']
    url += robot_api
    response = requests.post(url=url, json=data)
    if response.status_code!=200 or response.json()['status']!=1:
        logger.info(f"request chat algo {url} failed, data: {data}, return {response.status_code} {response.text}")
        return None
    
    logger.info(f"session {sess_id} got response: {response.json()['data']}")
    return response.json()['data']['message'], response.json()['data']['last_message_intent']
