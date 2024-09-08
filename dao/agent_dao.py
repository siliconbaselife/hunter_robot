from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.utils import deal_json_invaild
import json
import traceback
import re

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "new_history": "insert into agent_history_bank(manage_account_id, sess_id, prompt, tag, response, llm_type) values ('{}','{}','{}','{}','{}','{}')",
    "query_sess": "select distinct sess_id from agent_history_bank where manage_account_id='{}' and visible=1",
    'query_history': "select prompt, tag, response from agent_history_bank where sess_id='{}' and visible=1 order by id",
    'query_history_count': "select count(1) from agent_history_bank where sess_id='{}' and visible=1",
    'query_first_history': "select prompt, tag from agent_history_bank where sess_id='{}' and visible=1 limit 1",
    'mask_history': "update agent_history_bank set visible=0 where sess_id='{}'"
}


def new_agent_history_db(manage_account_id, sess_id, prompt, tag, response, llm_type):
    tag_str = json.dumps(tag, ensure_ascii=False)
    dbm.insert(
        sql_dict['new_history'].format(manage_account_id, sess_id, prompt.replace("'", " "), tag_str.replace("'", " "),
                                       response.replace("'", " "), llm_type))


def query_agent_sess_db(manage_account_id):
    return dbm.query(sql_dict['query_sess'].format(manage_account_id))


def query_agent_history_db(sess_id):
    return dbm.query(sql_dict['query_history'].format(sess_id))


def query_history_count_db(sess_id):
    return dbm.query(sql_dict['query_history_count'].format(sess_id))[0][0]


def query_first_history_db(sess_id):
    return dbm.query(sql_dict['query_first_history'].format(sess_id))[0]


def mask_history_db(sess_id):
    dbm.update(sql_dict['mask_history'].format(sess_id))


def update_chat_history_visible(user_id, session_id):
    sql = f"update chat_history_bank set visible = '0' where manage_account_id = '{user_id}' and session_id = '{session_id}'"
    dbm.update(sql)


def query_chat_history(user_id):
    sql = f"select session_id, history from chat_history_bank where manage_account_id = '{user_id}' and visible = '1'"
    return dbm.query(sql)


def get_history_msgs(user_id, session_id):
    sql = f"select history from chat_history_bank where manage_account_id = '{user_id}' and session_id = '{session_id}'"
    data = dbm.query(sql)
    if len(data) == 0:
        return None

    return data[0][0]


def update_history_msgs(user_id, session_id, history_msgs_str):
    history_msgs_str = history_msgs_str.replace("\'", "\\'")
    history_msgs_str = history_msgs_str.replace('\"', '\\"')
    history_msgs_str = history_msgs_str.replace('\n', '\\n')
    sql = f"update chat_history_bank set history = '{history_msgs_str}' where manage_account_id = '{user_id}' and session_id = '{session_id}'"
    dbm.update(sql)


def add_history_msgs(user_id, session_id, history_msgs_str):
    history_msgs_str = history_msgs_str.replace("\'", "\\'")
    history_msgs_str = history_msgs_str.replace('\"', '\\"')
    history_msgs_str = history_msgs_str.replace('\n', '\\n')
    sql = f"insert into chat_history_bank(manage_account_id, session_id, history) values('{user_id}', '{session_id}', '{history_msgs_str}')"
    dbm.insert(sql)
