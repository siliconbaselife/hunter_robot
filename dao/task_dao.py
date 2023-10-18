from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.utils import deal_json_invaild

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "register_job": "insert into job(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config, share, manage_account_id,robot_template) values ('{}','{}','{}','{}','{}','{}','{}', {}, '{}','{}')",
    "query_job_id": "select job_id from job where platform_type = '{}' and platform_id= '{}'",
    # "query_job_requirement": "select requirement_config from job where job_id = {}",
    "query_job_robotapi": "select robot_api from job where job_id='{}'",
    "register_account": "insert into account(account_id, platform_type, platform_id, jobs, task_config, description, manage_account_id) values ('{}','{}','{}','{}','{}','{}','{}')",
    "query_account_id": "select account_id from account where platform_type='{}' and platform_id='{}'",
    "query_account_type": "select platform_type from account where account_id='{}'",
    "get_jobs":"select jobs from account where account_id='{}'",
    "get_task":"select task_config from account where account_id='{}'",
    "new_candidate": "insert into candidate(candidate_id, candidate_name, age, degree, location, position, details) values ('{}','{}','{}','{}','{}','{}','{}')",
    "update_candidate_contact": "update candidate set contact='{}' where candidate_id='{}'",
    "query_candidate": "select candidate_id, candidate_name, age, degree, location, position, contact, details, filter_result from candidate where candidate_id='{}'",
    "query_chat_details": "select source, details, contact from chat where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "new_chat": "insert into chat(account_id, job_id, candidate_id, candidate_name, source, status, details, filter_result) values ('{}','{}','{}','{}','{}','{}','{}','{}')",
    "update_chat": "update chat set source='{}', status='{}', details='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "update_chat_only_details": "update chat set details='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "update_chat_contact": "update chat set contact='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "query_candidate_already_chat": "select status, source from chat where job_id='{}' and candidate_id='{}'",
    "add_task_count":"update account_exec_log set hello_sum_exec = hello_sum_exec+{} where account_id='{}' and job_id='{}' and exec_date='{}'",
    "insert_sub_task_log":"insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ('{}','{}','{}','{}')",
    "get_account_task_log":"select id, account_id, job_id, exec_date, hello_sum_need,hello_sum_exec,create_time, update_time from account_exec_log where account_id='{}' and exec_date='{}'",
    "get_job_task_log": "select id, account_id, job_id, exec_date, hello_sum_need,hello_sum_exec,create_time, update_time from account_exec_log where account_id='{}' and exec_date='{}'",
    "get_job_by_id":"select job_id,platform_type,platform_id,job_name,job_jd,robot_api,job_config,create_time,update_time,share,robot_api from job where job_id='{}'",
    "get_chats_by_job_id":"select account_id, job_id, candidate_id, candidate_name, source, status, contact, details, filter_result, create_time, update_time from chat where job_id='{}' and contact!='NULL' order by update_time desc limit {},{}",
    "get_chats_num_by_job_id":"select count(1) from chat where job_id='{}' and contact!='NULL'",
    "get_chats_by_ids":"select candidate_id, candidate_name, contact, details, filter_result, update_time, recall_cnt, job_id from chat where account_id='{}' and candidate_id in {} order by update_time desc",
    "recall_exec":"update chat set recall_cnt = recall_cnt + 1 where account_id='{}' and candidate_id='{}'",
    "add_friend_report":"update chat set added_friend=1 where account_id='{}' and candidate_id='{}'",
    "get_job_id_in_chat":"select job_id from chat where account_id='{}' and candidate_id='{}' order by create_time desc limit 1",
    "get_robot_template_by_job_id":"select robot_template from job where job_id='{}'",
    "get_independent_by_account_id":"select independent from account where account_id='{}'",
    "get_one_time_task_by_account_id":"select id,task_config from one_time_task where account_id='{}' and status = 0",
    "update_one_time_status_by_id":"update one_time_task set status={} where id={}"
}
def update_one_time_status_by_id(status, id):
    return dbm.update(sql_dict['update_one_time_status_by_id'].format(status, id))

def get_one_time_task_by_account_id(account_id):
    return dbm.query(sql_dict['get_one_time_task_by_account_id'].format(account_id))

def get_independent_by_account_id(account_id):
    return dbm.query(sql_dict['get_independent_by_account_id'].format(account_id))[0][0]

def get_robot_template_by_job_id(job_id):
    return dbm.query(sql_dict['get_robot_template_by_job_id'].format(job_id))[0][0]

def get_job_id_in_chat(account_id, candidate_id):
    return dbm.query(sql_dict['get_job_id_in_chat'].format(account_id, candidate_id))

def register_job_db(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config, share, manage_account_id, robot_template):
    if share == None:
        share = 0
    dbm.insert(sql_dict['register_job'].format(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config, share, manage_account_id,robot_template))
    return job_id

# def query_job_requirement_db(job_id):
#     return dbm.query(sql_dict['query_job_requirement'].format(job_id))

def query_job_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_job_id'].format(platform_type, platform_id))[0][0]

def query_robotapi_db(job_id):
    return dbm.query(sql_dict['query_job_robotapi'].format(job_id))[0][0]

def register_account_db(account_id, platform_type, platform_id, jobs, task_config, desc, manage_account_id):
    # d = [[account_id, platform_type, platform_id, jobs, task_config]]
    dbm.insert(sql_dict['register_account'].format(account_id, platform_type, platform_id, jobs, task_config, desc, manage_account_id))
    return account_id

def query_account_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_account_id'].format(platform_type, platform_id))[0][0]

def query_account_type_db(account_id):
    return dbm.query(sql_dict['query_account_type'].format(account_id))[0][0]

def new_candidate_db(candidate_id, candidate_name, age, degree, location, position, details):
    details = deal_json_invaild(details)
    try:
        dbm.insert(sql_dict['new_candidate'].format(candidate_id, candidate_name, age, degree, location, position, details))
    except BaseException as e:
        logger.info(f'new_candidate_error, (msg: {details})')
def query_candidate_exist(candidate_id):
    return len(dbm.query(sql_dict['query_candidate'].format(candidate_id)))>0

def query_candidate_name_and_filter_result(candidate_id):
    item = dbm.query(sql_dict['query_candidate'].format(candidate_id))[0]
    return item[1], item[8]
def query_candidate_by_id(candidate_id):
    return dbm.query(sql_dict['query_candidate'].format(candidate_id))

def update_candidate_contact_db(candidate_id, contact):
    dbm.update(sql_dict['update_candidate_contact'].format(contact, candidate_id))

def new_chat_db(account_id, job_id, candidate_id, candidate_name, source=None, status='init', details=None, filter_result=None):
    dbm.insert(sql_dict['new_chat'].format(account_id, job_id, candidate_id, candidate_name, source, status, details, filter_result))

def query_chat_db(account_id, job_id, candidate_id):
    return dbm.query(sql_dict['query_chat_details'].format(account_id, job_id, candidate_id))

def update_chat_db(account_id, job_id, candidate_id, source, status, details):
    dbm.update(sql_dict['update_chat'].format(source, status, details, account_id, job_id, candidate_id))

def update_chat_only_details_db(account_id, job_id, candidate_id, details):
    dbm.update(sql_dict['update_chat_only_details'].format(details, account_id, job_id, candidate_id))

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

def get_job_task_log_db(account_id, exec_date):
    return dbm.query(sql_dict["get_job_task_log"].format(account_id, exec_date))

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
    s = "('" + "','".join(candidate_ids) + "')"
    # logger.info(f"test_sql, {s}")
    return dbm.query(sql_dict["get_chats_by_ids"].format(account_id, s))

def add_recall_count(account_id, candidate_id):
    return dbm.query(sql_dict["recall_exec"].format(account_id, candidate_id))

def add_friend_report(account_id, candidate_id):
    dbm.update(sql_dict['add_friend_report'].format(account_id, candidate_id))