from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.db_manager import dbm

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "update_chat_status_by_id": "update wechat_chat set status={} where wechat_account_id='{}' and wechat_id='{}'",
    "update_chat_status_by_alias_id": "update wechat_chat set status={} where wechat_account_id='{}' and wechat_alias_id='{}'",
    "get_chat_by_alias_id": "select candidate_id,candidate_name,wechat_id,wechat_alias_id,wechat_account_id,details,status from wechat_chat where wechat_alias_id='{}' and wechat_account_id='{}'",
    "update_detail": "update wechat_chat set detail='{}' where wechat_account_id='{}' and wechat_alias_id='{}'",
    "get_wechat_account_info": "select wechat_account_id, task_config from wechat_account where wechat_account_id='{}'",
    "get_candidate_update_last_hour": "select job_id, candidate_id, candidate_name, contact from chat where job_id = '{}' and contact!='NULL' and update_time > DATE_SUB(NOW(), INTERVAL 60 MINUTE)"
}
    
def friend_status_update_by_id(wechat_account_id, wechat_id, status):
    return dbm.update(sql_dict['update_chat_status_by_id'].format(status, wechat_account_id, wechat_id))
def friend_status_update_by_alias_id(wechat_account_id, wechat_alias_id, status):
    return dbm.update(sql_dict['update_chat_status_by_alias_id'].format(status, wechat_account_id, wechat_alias_id))

def get_chat_by_alias_id(wechat_alias_id, wechat_account_id):
    return dbm.query(sql_dict["get_chat_by_alias_id"].format(wechat_alias_id, wechat_account_id))[0]

def update_detail(wechat_alias_id, wechat_account_id, detail):
    return dbm.update(sql_dict["update_detail"].format(wechat_alias_id, wechat_account_id))

def get_wechat_account_info(wechat_account_id):
    return dbm.query(sql_dict["get_wechat_account_info"].format(wechat_account_id))[0]

def get_candidate_update_last_hour():
    return
