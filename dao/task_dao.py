from utils.db_manager import dbm
import uuid

sql_dict = {
    "register_job": "insert into job(job_id, job_name, job_jd, robot_api) values ({},{},{},{})",
    "query_job_id": "select job_id from job where job_name = {}",
    "query_job_robotapi": "select robot_api from job where job_id={}",
    "register_account": "insert into account(account_id, platform_type, platform_id, jobs, task_config) values ({},{},{},{},{}})",
    "query_account_id": "select account_id from account where platform_type={} and platform_id={}",
    "new_candidate": "insert into candidate(candidate_id, candidate_name, age, education, details) values ({},{},{},{},{})",
    "new_chat": "insert into chat(account_id, job_id, candidate_id, candidate_name, source, status, details) values ({},{},{},{},{},{},{}})",
    "update_chat": "update chat set status={}, details={} where account_id={} and job_id={} and candidate_id={}",
    "query_chat": "select status, source from chat where job_id={} and candidate_id={}",
    "add_task_count":"update account_exec_log set hello_sum_exec = hello_sum_exec+1 where account_id={} and job_id={} and exec_date={}",
    "get_task":"select * from account_config where account_id={}",
    "insert_sub_task_log":"insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ({},{},{},{})"
}

def register_job(job_name, job_jd, robot_api):
    job_id = str(uuid.uuid1())
    d = [[job_id, job_name, job_jd, robot_api]]
    dbm.insert(sql_dict['register_job'], d)
    return job_id

def query_job_id(job_name):
    return dbm.query(sql_dict['query_job_id'].format(job_name))[0][0]

def query_robotapi(job_id):
    return dbm.query(sql_dict['query_job_robotapi'].format(job_id))[0][0]

def register_account(platform_type, platform_id, jobs, task_config):
    account_id = str(uuid.uuid1())
    d = [[account_id, platform_type, platform_id, jobs, task_config]]
    dbm.insert(sql_dict['register_account'], d)
    return account_id

def query_account_id(platform_type, platform_id):
    return dbm.query(sql_dict['query_account_id'].format(platform_type, platform_id))[0][0]

def new_candidate(candidate_id, candidate_name, age, education, details):
    d = [[candidate_id, candidate_name, age, education, details]]
    dbm.insert(sql_dict['new_candidate'], d)

def new_chat(account_id, job_id, candidate_id, candidate_name, source, status='init', details=None):
    d = [[account_id, job_id, candidate_id, candidate_name, source, status, details]]
    dbm.insert(sql_dict['new_chat'], d)

def update_chat(account_id, job_id, candidate_id, status, details):
    dbm.update(sql_dict['update_chat'].format(status, details, account_id, job_id, candidate_id))

def is_chatting(job_id, candidate_id):
    ret = dbm.query(sql_dict['query_chat'].format(job_id, candidate_id))
    return len(ret)>0

def get_task(account_id):
    return dbm.query(sql_dict["get_task"].format(account_id))

def init_task_log(account_id, job_id, exec_date, hello_sum_need):
    d = [[account_id, job_id, exec_date, hello_sum_need]]
    return dbm.insert(sql_dict["insert_sub_task_log"], d)

def hello_exec(account_id, job_id, exec_date):
    return dbm.update(sql_dict["add_task_count"].format(account_id, job_id, exec_date))