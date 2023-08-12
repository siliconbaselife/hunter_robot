from utils.db_manager import dbm
import uuid
from utils.config import config
from utils.log import get_logger

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "register_job": "insert into job(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config) values ('{}','{}','{}','{}','{}','{}','{}')",
    "query_job_id": "select job_id from job where platform_type = '{}' and platform_id= '{}'",
    # "query_job_requirement": "select requirement_config from job where job_id = {}",
    "query_job_robotapi": "select robot_api from job where job_id='{}'",
    "register_account": "insert into account(account_id, platform_type, platform_id, jobs, task_config, description) values ('{}','{}','{}','{}','{}','{}')",
    "query_account_id": "select account_id from account where platform_type='{}' and platform_id='{}'",
    "query_account_type": "select platform_type from account where account_id='{}'",
    "get_jobs":"select jobs from account where account_id='{}'",
    "get_task":"select task_config from account where account_id='{}'",
    "new_candidate": "insert into candidate(candidate_id, candidate_name, age, degree, location, position, details) values ('{}','{}','{}','{}','{}','{}','{}')",
    "update_candidate_contact": "update candidate set contact='{}' where candidate_id='{}'",
    "query_candidate": "select candidate_name, age, degree, location, position, contact, details from candidate where candidate_id='{}'",
    "query_chat_details": "select source, details, contact from chat where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "new_chat": "insert into chat(account_id, job_id, candidate_id, candidate_name, source, status, details) values ('{}','{}','{}','{}','{}','{}','{}')",
    "update_chat": "update chat set source='{}', status='{}', details='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "update_chat_contact": "update chat set contact='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "query_candidate_already_chat": "select status, source from chat where job_id='{}' and candidate_id='{}'",
    "add_task_count":"update account_exec_log set hello_sum_exec = hello_sum_exec+{} where account_id='{}' and job_id='{}' and exec_date='{}'",
    "insert_sub_task_log":"insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ('{}','{}','{}','{}')",
    "get_account_task_log":"select * from account_exec_log where account_id='{}' and exec_date='{}'",
    "get_job_task_log": "select * from account_exec_log where where account_id='{}' and job_id='{}' and exec_date='{}'",
    "get_job_by_id":"select * from job where job_id='{}'",
    "get_chats_by_job_id":"select * from chat where job_id='{}' and contact!='NULL' order by update_time desc limit {},{}",
    "get_chats_num_by_job_id":"select count(1) from chat where job_id='{}' and contact!='NULL'",
    "get_chats_by_ids":"select candidate_id, candidate_name, contact, details, filter_result, update_time, recall_cnt from chat where account_id={} and candidate_id in {}",
    "recall_exec":"update chat set recall_cnt = recall_cnt + 1 where account_id='{}' and candidate_id='{}'"
}

def register_job_db(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config):
    dbm.insert(sql_dict['register_job'].format(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config))
    return job_id

# def query_job_requirement_db(job_id):
#     return dbm.query(sql_dict['query_job_requirement'].format(job_id))

def query_job_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_job_id'].format(platform_type, platform_id))[0][0]

def query_robotapi_db(job_id):
    return dbm.query(sql_dict['query_job_robotapi'].format(job_id))[0][0]

def register_account_db(account_id, platform_type, platform_id, jobs, task_config, desc):
    # d = [[account_id, platform_type, platform_id, jobs, task_config]]
    dbm.insert(sql_dict['register_account'].format(account_id, platform_type, platform_id, jobs, task_config, desc))
    return account_id

def query_account_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_account_id'].format(platform_type, platform_id))[0][0]

def query_account_type_db(account_id):
    return dbm.query(sql_dict['query_account_type'].format(account_id))[0][0]

def new_candidate_db(candidate_id, candidate_name, age, degree, location, position, details):
    dbm.insert(sql_dict['new_candidate'].format(candidate_id, candidate_name, age, degree, location, position, details))

def query_candidate_exist(candidate_id):
    return len(dbm.query(sql_dict['query_candidate'].format(candidate_id)))>0

def query_candidate_name(candidate_id):
    return dbm.query(sql_dict['query_candidate'].format(candidate_id))[0][0]

def update_candidate_contact_db(candidate_id, contact):
    dbm.update(sql_dict['update_candidate_contact'].format(contact, candidate_id))

def new_chat_db(account_id, job_id, candidate_id, candidate_name, source=None, status='init', details=None):
    # d = [[account_id, job_id, candidate_id, candidate_name, source, status, details]]
    dbm.insert(sql_dict['new_chat'].format(account_id, job_id, candidate_id, candidate_name, source, status, details))

def query_chat_db(account_id, job_id, candidate_id):
    return dbm.query(sql_dict['query_chat_details'].format(account_id, job_id, candidate_id))

def update_chat_db(account_id, job_id, candidate_id, source, status, details):
    dbm.update(sql_dict['update_chat'].format(source, status, details, account_id, job_id, candidate_id))

def update_chat_contact_db(account_id, job_id, candidate_id, contact):
    dbm.update(sql_dict['update_chat_contact'].format(contact, account_id, job_id, candidate_id))

def is_chatting_db(job_id, candidate_id):
    ret = dbm.query(sql_dict['query_candidate_already_chat'].format(job_id, candidate_id))
    return len(ret)>0

def get_account_jobs_db(account_id):
    return dbm.query(sql_dict["get_jobs"].format(account_id))[0][0]

def get_account_task_db(account_id):
    return dbm.query(sql_dict["get_task"].format(account_id))[0][0]

def init_task_log_db(account_id, job_id, exec_date, hello_sum_need):
    # d = [[account_id, job_id, exec_date, hello_sum_need]]
    dbm.insert(sql_dict["insert_sub_task_log"].format(account_id, job_id, exec_date, hello_sum_need))

def get_account_task_log_db(account_id, exec_date):
    return dbm.query(sql_dict["get_account_task_log"].format(account_id, exec_date))

def get_job_task_log_db(account_id, job_id, exec_date):
    return dbm.query(sql_dict["get_job_task_log"].format(account_id, job_id, exec_date))

##打招呼那个接口要调一下，这个记录一下
def hello_exec_db(account_id, job_id, exec_date, hello_cnt=1):
    dbm.update(sql_dict["add_task_count"].format(hello_cnt, account_id, job_id, exec_date))

def get_job_by_id(job_id):
    return dbm.query(sql_dict["get_job_by_id"].format(job_id))

def get_chats_by_job_id(job_id, start, limit):
    return dbm.query(sql_dict["get_chats_by_job_id"].format(job_id, start, limit))

def get_chats_num_by_job_id(job_id):
    return dbm.query(sql_dict["get_chats_num_by_job_id"].format(job_id))

def get_chats_by_ids(account_id, candidate_ids):
    return dbm.query(sql_dict["get_chats_by_ids"].format(account_id, '("' + '","'.join(candidate_ids) + '")'))

def add_recall_count(account_id, candidate_id):
    return dbm.query(sql_dict["recall_exec"].format(account_id, candidate_id))