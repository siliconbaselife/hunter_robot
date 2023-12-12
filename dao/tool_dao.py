from utils.db_manager import dbm
import uuid
from utils.config import config
from utils.log import get_logger
import json

logger = get_logger(config['log']['log_file'])

sql_dict = {
    "get_undo_filter_task":"select id,manage_account_id, jd, resume_url from resume_filter_task where status=0",
    "update_filter_task_status":"update resume_filter_task set status={} where id={} ",
    "get_filter_task_by_manage_id": "select id, manage_account_id, resume_url, status, create_time,jd,filter_result,taskname from resume_filter_task where manage_account_id='{}'",
    "create_new_filter_task": "insert into resume_filter_task(manage_account_id, jd, resume_url,taskname) values ('{}', '{}', '{}','{}')",
    "update_filter_result":"update resume_filter_task set filter_result='{}' where id={}",
    "get_filter_task_by_id":"select id, manage_account_id, resume_url, status, create_time,jd,filter_result,taskname from resume_filter_task where id={}",
    "upload_online_profile":"insert into online_resume(manage_account_id, platform, raw_profile, candidate_id) values ('{}', '{}', '{}', '{}')"
}
def upload_online_profile(manage_account_id, platform, raw_profile, candidate_id):
    raw_profile = raw_profile.replace("\n", "\\n")
    raw_profile = raw_profile.replace("\'", "\\'")
    raw_profile = raw_profile.replace('\"', '\\"')
    return dbm.insert(sql_dict['upload_online_profile'].format(manage_account_id, platform, raw_profile, candidate_id))

def get_filter_task_by_id(task_id):
    return dbm.query(sql_dict['get_filter_task_by_id'].format(task_id))

def get_filter_task_by_manage_id(manage_account_id):
    return dbm.query(sql_dict['get_filter_task_by_manage_id'].format(manage_account_id))

def get_undo_filter_task():
    return dbm.query(sql_dict['get_undo_filter_task'])

def update_filter_task_status(status, task_id):
    return dbm.update(sql_dict['update_filter_task_status'].format(status, task_id))

def create_new_filter_task(manage_account_id, jd, resume_url, taskname):
    return dbm.insert(sql_dict['create_new_filter_task'].format(manage_account_id, jd, resume_url,taskname))

def update_filter_result(filter_result, id):
    filter_result = filter_result.replace("\n", "\\n")
    filter_result = filter_result.replace("\'", "\\'")
    filter_result = filter_result.replace('\"', '\\"')
    return dbm.update(sql_dict['update_filter_result'].format(filter_result, id))