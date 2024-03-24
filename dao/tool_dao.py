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
    "update_filter_result":"update resume_filter_task set filter_result='{}', format_resumes = '{}' where id={}",
    "get_filter_task_by_id":"select id, manage_account_id, resume_url, status, create_time,jd,filter_result,taskname, format_resumes from resume_filter_task where id={}",
    "upload_online_profile":"insert into online_resume(manage_account_id, platform, raw_profile, candidate_id) values ('{}', '{}', '{}', '{}')",
    "update_raw_profile":"update online_resume set raw_profile='{}' where manage_account_id='{}' and platform = '{}' and candidate_id='{}'",
    "upload_online_profile_pdf":"insert into online_resume(manage_account_id, platform, cv_url, candidate_id) values ('{}', '{}', '{}', '{}')",
    "get_resume_by_candidate_id_and_platform":"select id,candidate_id,manage_account_id,platform,create_time from online_resume where candidate_id='{}' and platform='{}' and manage_account_id='{}'",
    "get_raw_latest_profile_by_candidate_id_and_platform": "select raw_profile from online_resume where candidate_id = '{}' and platform = '{}' order by id desc limit 1;",
    "get_resume_by_filter":"select id,candidate_id,manage_account_id,platform,create_time,raw_profile from online_resume where manage_account_id='{}' and platform='{}' and create_time > '{}' and create_time < '{}'",
    "get_resume_by_list":"select id,candidate_id,manage_account_id,platform,create_time,raw_profile from online_resume where manage_account_id='{}' and platform='{}' and create_time > '{}' and create_time < '{}' and list_name='{}'",
    "create_conversation_report" : "insert into conversation_report (candidate_id, platform, contact, conversation) values ('{}', '{}', '{}', '{}')",
    "add_resume_list_db":"insert into resume_list(manage_account_id, platform, list_name) values ('{}', '{}', '{}')",
    "get_resume_list_db":"select list_name from resume_list where manage_account_id='{}' and platform='{}'",
    "add_list_relation":"insert into resume_list_relation(manage_account_id, list_name, candidate_id) values ('{}', '{}', '{}')"
}
def add_list_relation(manage_account_id, list_name, candidate_id):
    return dbm.insert(sql_dict['add_list_relation'].format(manage_account_id, list_name, candidate_id))
    
def get_resume_list_db(manage_account_id, platform):
    return dbm.query(sql_dict['get_resume_list_db'].format(manage_account_id, platform))

def add_resume_list_db(manage_account_id, platform, list_name):
    return dbm.insert(sql_dict['add_resume_list_db'].format(manage_account_id, platform, list_name))

def get_resume_by_filter(manage_account_id, platform, start_date, end_date, list_name):
    if list_name == '':
        return dbm.query(sql_dict['get_resume_by_filter'].format(manage_account_id, platform, start_date, end_date))
    else:
        return dbm.query(sql_dict['get_resume_by_list'].format(manage_account_id, platform, start_date, end_date, list_name))

def get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id):
    return dbm.query(sql_dict['get_resume_by_candidate_id_and_platform'].format(candidate_id, platform, manage_account_id))

def get_raw_latest_profile_by_candidate_id_and_platform(candidate_id, platform):
    return dbm.query(sql_dict['get_raw_latest_profile_by_candidate_id_and_platform'].format(candidate_id, platform))

def upload_online_profile(manage_account_id, platform, raw_profile, candidate_id):
    raw_profile = raw_profile.replace("\n", "\\n")
    raw_profile = raw_profile.replace("\'", "\\'")
    raw_profile = raw_profile.replace('\"', '\\"')
    if len(get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id)) > 0:
        return dbm.update(sql_dict['update_raw_profile'].format(raw_profile, manage_account_id, platform, candidate_id))
    else:
        return dbm.insert(sql_dict['upload_online_profile'].format(manage_account_id, platform, raw_profile, candidate_id))
def upload_online_profile_pdf(manage_account_id, platform, candidate_id, cv_addr):
    return dbm.insert(sql_dict['upload_online_profile_pdf'].format(manage_account_id, platform, cv_addr, candidate_id))


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

def update_filter_result(filter_result, format_resumes, id):
    filter_result = filter_result.replace("\n", "\\n")
    filter_result = filter_result.replace("\'", "\\'")
    filter_result = filter_result.replace('\"', '\\"')

    format_resumes = format_resumes.replace("\n", "\\n")
    format_resumes = format_resumes.replace("\'", "\\'")
    format_resumes = format_resumes.replace('\"', '\\"')
    return dbm.update(sql_dict['update_filter_result'].format(filter_result, format_resumes, id))

def create_conversation_report(candidate_id, platform, contact, conversations):
    contact_str = json.dumps(contact, ensure_ascii=False)
    contact_str = contact_str.replace("\n", "\\n")
    contact_str = contact_str.replace("\'", "\\'")
    contact_str = contact_str.replace('\"', '\\"')

    conversations_str = json.dumps(conversations, ensure_ascii=False)
    conversations_str = conversations_str.replace("\n", "\\n")
    conversations_str = conversations_str.replace("\'", "\\'")
    conversations_str = conversations_str.replace('\"', '\\"')
    return dbm.insert(sql_dict['create_conversation_report'].format(candidate_id, platform, contact_str, conversations_str))