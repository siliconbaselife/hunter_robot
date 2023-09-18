from utils.db_manager import dbm
import uuid
from utils.config import config
from utils.log import get_logger
import json

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "login_check":"select manage_account_id,password from manage_account where manage_account_id='{}'",
    "jobs_query":"select jobs from account where account_id='{}'",
    "jobs_update":"update account set jobs='{}' where account_id='{}'",
    "my_job_list_db": "select job_id, job_name, share, job_config, platform_type,robot_api from job where manage_account_id='{}'",
    "my_account_list_db": "select account_id, platform_type, description, jobs, task_config from account where manage_account_id='{}'",
    "account_config_update_db": "update account set task_config='{}',jobs='{}' where manage_account_id='{}' and account_id='{}'",
    "update_job_config": "update job set robot_api='{}',job_config='{}' where job_id='{}'",
    "manage_config":"select config from manage_account where manage_account_id='{}'"
}
    
def get_manage_config_db(manage_account_id):
    return dbm.query(sql_dict['manage_config'].format(manage_account_id))[0][0]

def login_check_db(user_name):
    return dbm.query(sql_dict['login_check'].format(user_name))

def jobs_query(account_id):
    jobs = dbm.query(sql_dict['jobs_query'].format(account_id))[0][0]
    # logger.info(f"test_jobs: {jobs}")
    return json.loads(jobs)

def jobs_update(jobs, account_id):
    return dbm.update(sql_dict['jobs_update'].format(jobs, account_id))

def my_job_list_db(manage_account_id):
    return dbm.query(sql_dict['my_job_list_db'].format(manage_account_id))

def my_account_list_db(manage_account_id):
    return dbm.query(sql_dict['my_account_list_db'].format(manage_account_id))

def account_config_update_db(manage_account_id, account_id, task_config_json, job_list_json):
    return dbm.update(sql_dict['account_config_update_db'].format(task_config_json, job_list_json, manage_account_id, account_id))

def update_job_config(job_id,robot_api, job_config):
    return dbm.update(sql_dict['update_job_config'].format(robot_api, job_config, job_id))
