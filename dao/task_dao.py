from utils.db_manager import dbm
import uuid

sql_dict = {
    "register_job": "insert into job(job_id, job_name, requirement_config, job_jd, robot_api) values ({},{},{},{},{})",
    "query_job_id": "select job_id from job where job_name = {}",
    "query_job_requirement": "select requirement_config from job where job_id = {}",
    "query_job_robotapi": "select robot_api from job where job_id={}",
    "register_account": "insert into account(account_id, platform_type, platform_id, jobs, task_config) values ({},{},{},{},{}})",
    "query_account_id": "select account_id from account where platform_type={} and platform_id={}",
    "new_candidate": "insert into candidate(candidate_id, candidate_name, age, education, details) values ({},{},{},{},{})",
    "update_candidate_contact": "update candidate set contact={} where candidate_id={}",
    "query_candidate": "select desc from candidate where candidate_id={}",
    "query_chat_details": "select source, details from chat where account_id={} and job_id={} and candidate_id={}",
    "new_chat": "insert into chat(account_id, job_id, candidate_id, candidate_name, source, status, details) values ({},{},{},{},{},{},{}})",
    "update_chat": "update chat set source={}, status={}, details={} where account_id={} and job_id={} and candidate_id={}",
    "update_chat_contact": "update chat set contact={} where account_id={} and job_id={} and candidate_id={}",
    "query_candidate_already_chat": "select status, source from chat where job_id={} and candidate_id={}",
    "add_task_count":"update account_exec_log set hello_sum_exec = hello_sum_exec+1 where account_id={} and job_id={} and exec_date={}",
    "get_task":"select * from account_config where account_id={}",
    "insert_sub_task_log":"insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ({},{},{},{})",
    "get_sub_task_with_account_id":"select * from account_exec_log where account_id={} and exec_date={}"
}

def register_job_db(job_name, job_requirement_config, job_jd, robot_api):
    job_id = str(uuid.uuid1())
    d = [[job_id, job_name, job_requirement_config, job_jd, robot_api]]
    dbm.insert(sql_dict['register_job'], d)
    return job_id

def query_job_requirement_db(job_id):
    return dbm.query(sql_dict['query_job_requirement'].format(job_id))

def query_job_id_db(job_name):
    return dbm.query(sql_dict['query_job_id'].format(job_name))[0][0]

def query_robotapi_db(job_id):
    return dbm.query(sql_dict['query_job_robotapi'].format(job_id))[0][0]

def register_account_db(platform_type, platform_id, jobs, task_config):
    account_id = str(uuid.uuid1())
    d = [[account_id, platform_type, platform_id, jobs, task_config]]
    dbm.insert(sql_dict['register_account'], d)
    return account_id

def query_account_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_account_id'].format(platform_type, platform_id))[0][0]

def new_candidate_db(candidate_id, candidate_name, age, education, details):
    d = [[candidate_id, candidate_name, age, education, details]]
    dbm.insert(sql_dict['new_candidate'], d)

def query_candidate_exist(candidate_id):
    return len(dbm.query(sql_dict['query_candidate'].format(candidate_id)))>0

def update_candidate_contact_db(candidate_id, contact):
    dbm.update(sql_dict['update_candidate_contact'].format(contact, candidate_id))

def new_chat_db(account_id, job_id, candidate_id, candidate_name, source=None, status='init', details=None):
    d = [[account_id, job_id, candidate_id, candidate_name, source, status, details]]
    dbm.insert(sql_dict['new_chat'], d)

def query_chat_db(account_id, job_id, candidate_id):
    return dbm.query(sql_dict['query_chat_details'].format(account_id, job_id, candidate_id))

def update_chat_db(account_id, job_id, candidate_id, source, status, details):
    dbm.update(sql_dict['update_chat'].format(source, status, details, account_id, job_id, candidate_id))

def update_chat_contact_db(account_id, job_id, candidate_id, contact):
    dbm.update(sql_dict['update_chat_contact'].format(contact, account_id, job_id, candidate_id))

def is_chatting_db(job_id, candidate_id):
    ret = dbm.query(sql_dict['query_candidate_already_chat'].format(job_id, candidate_id))
    return len(ret)>0

def get_task_db(account_id):
    return dbm.query(sql_dict["get_task"].format(account_id))

def init_task_log_db(account_id, job_id, exec_date, hello_sum_need):
    d = [[account_id, job_id, exec_date, hello_sum_need]]
    return dbm.insert(sql_dict["insert_sub_task_log"], d)

def get_sub_task_with_account_id_db(account_id, exec_date):
    return dbm.query(sql_dict["get_sub_task_with_account_id"].format(account_id, exec_date))

##打招呼那个接口要调一下，这个记录一下
def hello_exec_db(account_id, job_id, exec_date):
    return dbm.update(sql_dict["add_task_count"].format(account_id, job_id, exec_date))