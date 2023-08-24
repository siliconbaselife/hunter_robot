from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "update_chat_status": "update wechat_chat set status={} where wechat_account_id={} and wechat_id={}",
    "get_chat_by_wechat_id": "select candidate_id,candidate_name,wechat_id,wechat_alias_id,wechat_account_id,details,status from wechat_chat where wechat_alias_id={} and wechat_account_id={}"
}
    
def friend_status_update(wechat_account_id, wechat_id, status):
    return sql_dict['update_chat_status'].format(status, wechat_account_id, wechat_id)

def get_chat_by_wechat_id(wechat_alias_id, wechat_account_id):
    return sql_dict["get_chat_by_wechat_id"].format(wechat_alias_id, wechat_account_id)[0]

def msg_append():
    return

def wechat_chat():
    
    return