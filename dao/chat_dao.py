from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.db_manager import dbm
import json

logger = get_logger(config['log']['log_file'])


def query_conf(user_id, tag):
    sql = f"select * from user_chat_conf where manage_account_id = '{user_id}' and tag = '{tag}'"
    data = dbm.query(sql)
    if len(data) == 0:
        return None

    conf = json.loads(data[0][3])

    return conf


def add_conf(user_id, tag, content):
    sql = f"insert into user_chat_conf(manage_account_id, tag, content) values('{user_id}', '{tag}', '{json.dumps(content)}')"
    dbm.insert(sql)


def update_conf(user_id, tag, content):
    sql = f"update user_chat_conf set content = '{json.dumps(content)}' where user_id = '{user_id}' and tag = '{tag}'"
    dbm.update(sql)


def query_confs(user_id):
    sql = f"select * from user_chat_conf where manage_account_id = '{user_id}'"
    data = dbm.query(sql)
    confs = []
    for i in range(len(data)):
        confs.append({
            'manage_account_id': data[i][1],
            'tag': data[i][2],
            'content': json.loads(data[i][3])
        })

    return confs


def query_chat(user_id, account_id, candidate_id):
    sql = f"select * from user_chat_history where user_id = '{user_id}' and account_id = '{account_id}' and candidate_id = '{candidate_id}'"
    data = dbm.query(sql)
    if len(data) == 0:
        return None

    details = json.loads(data[0]["details"])
    return details


def add_chat(user_id, account_id, candidate_id, details):
    sql = f"insert into user_chat_history(manage_account_id, account_id, candidate_id, details) values('{user_id}', '{account_id}', '{candidate_id}', '{json.dumps(details)}')"
    dbm.insert(sql)


def update_chat(user_id, account_id, candidate_id, details):
    sql = f"update user_chat_history set where manage_account_id = '{user_id}' and account_id = '{account_id}' and candidate_id = '{candidate_id}' and details = '{details}'"
    dbm.update(sql)
