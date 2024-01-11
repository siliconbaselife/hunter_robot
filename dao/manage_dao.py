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
    "my_job_list_db": "select job_id, job_name, share, job_config, platform_type,robot_api, robot_template from job where manage_account_id='{}'",
    "my_account_list_db": "select account_id, platform_type, description, jobs, task_config from account where manage_account_id='{}' and ver='{}'",
    "account_config_update_db": "update account set task_config='{}',jobs='{}' where manage_account_id='{}' and account_id='{}'",
    "update_job_config": "update job set robot_api='{}',job_config='{}',robot_template='{}' where job_id='{}'",
    "only_update_job_config":"update job set job_config='{}' where job_id='{}'",
    "manage_config":"select config from manage_account where manage_account_id='{}'",
    "get_jobs_task_by_id":"select jobs, task_config from account where account_id='{}'",
    "get_llm_template_by_manage_id":"select template_name, template_id, template_config from llm_template where manage_account_id='{}'",
    "get_llm_config_by_id":"select template_config from llm_template where template_id='{}'",
    "update_llm_template":"update llm_template set template_name='{}',template_config='{}' where template_id='{}'",
    "insert_llm_template":"insert into llm_template(manage_account_id, template_id, template_name, template_config) values ('{}', '{}', '{}', '{}')",
    "get_chat_count_by_job": "select date_format(`create_time`, '%Y-%m-%d'),count(1),sum(case when contact!='' then 1 else 0 end) from chat where create_time > date_sub(curdate(), interval 7 day) and job_id='{}' group by date_format(`create_time`, '%Y-%m-%d')",
    "get_job_name_by_id":"select job_name from job where job_id='{}'",
    "manage_account_register":"insert into manage_account(manage_account_id, password, `desc`, config) values ('{}', '{}', '{}', '{}')",
    "delete_job_db":"delete from job where job_id='{}'",
    "delete_template_db":"delete from llm_template where template_id='{}'",
    "get_hello_ids":"select candidate_id from hello_record where manage_account_id = '{}' and status = 1 and platform='{}'",
    "delete_hello_ids":"delete from hello_record where manage_account_id='{}' and platform='{}' and status = 1",
    "insert_hello_id":"insert into hello_record(manage_account_id, candidate_id, platform, status) values ('{}', '{}','{}', 1)",
    "hello_sent":"update hello_record set status=2 where manage_account_id='{}' and candidate_id in {}",
    "get_all_hello_ids":"select candidate_id,platform from hello_record where manage_account_id = '{}' and status = 1",
    "get_profile_by_id":"select raw_profile from online_resume where candidate_id='{}' order by id desc limit 1"
} 

def get_profile_by_id(candidate_id):
    return dbm.query(sql_dict['get_profile_by_id'].format(candidate_id))


def hello_sent_db(manage_account_id, candidate_ids):
    if len(candidate_ids) > 0:
        candidate_ids_p = [c for c in candidate_ids if c != '']
        s = "('" + "','".join(candidate_ids_p) + "')"
        return dbm.update(sql_dict['hello_sent'].format(manage_account_id, s))
    return ''

def get_all_hello_ids_db(manage_account_id):
    return dbm.query(sql_dict['get_all_hello_ids'].format(manage_account_id))

def get_hello_ids(manage_account_id, platform):
    return dbm.query(sql_dict['get_hello_ids'].format(manage_account_id, platform))

def update_hello_ids(manage_account_id, candidate_ids, platform):
    dbm.delete(sql_dict['delete_hello_ids'].format(manage_account_id, platform))
    for c in candidate_ids:
        dbm.insert(sql_dict['insert_hello_id'].format(manage_account_id, c, platform))

def delete_job_db(job_id):
    return dbm.delete(sql_dict['delete_job_db'].format(job_id))

def delete_template_db(template_id):
    return dbm.delete(sql_dict['delete_template_db'].format(template_id))

def manage_account_register(passwd, email, desc, c_j):
    c_j = c_j.replace("\'", "\\'")
    c_j = c_j.replace('\"', '\\"')
    return dbm.insert(sql_dict['manage_account_register'].format(email, passwd, desc, c_j))

def get_job_name_by_id(job_id):
    return dbm.query(sql_dict['get_job_name_by_id'].format(job_id))[0][0]

def get_chat_count_by_job(job_id):
    chat_count = dbm.query(sql_dict['get_chat_count_by_job'].format(job_id))
    if len(chat_count) == 0:
        return []
    else:
        return chat_count

def update_llm_template(template_name, template_config, template_id):
    return dbm.update(sql_dict['update_llm_template'].format(template_name, template_config, template_id))

def insert_llm_template(manage_account_id, template_id, template_name, template_config):
    template_config = template_config.replace("\'", "\\'")
    template_config = template_config.replace('\"', '\\"')
    return dbm.insert(sql_dict['insert_llm_template'].format(manage_account_id, template_id, template_name, template_config))

def get_llm_config_by_id_db(template_id):
    return  dbm.query(sql_dict['get_llm_config_by_id'].format(template_id))[0][0]

def get_llm_template_by_manage_id_db(manage_account_id):
    return  dbm.query(sql_dict['get_llm_template_by_manage_id'].format(manage_account_id))

def get_jobs_task_by_id(account_id):
    return  dbm.query(sql_dict['get_jobs_task_by_id'].format(account_id))[0]

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
    return dbm.query(sql_dict['my_account_list_db'].format(manage_account_id, 'v1'))

def my_account_list_db_v2(manage_account_id, ver):
    return dbm.query(sql_dict['my_account_list_db'].format(manage_account_id, ver))

def account_config_update_db(manage_account_id, account_id, task_config_json, job_list_json):
    task_config_json = task_config_json.replace('\\n',',')
    task_config_json = task_config_json.replace("\'", "\\'")
    sql = sql_dict['account_config_update_db'].format(task_config_json, job_list_json, manage_account_id, account_id)
    # sql = "update account set task_config='" + task_config_json + "',jobs='" + job_list_json + "' where manage_account_id='" + manage_account_id + "' and account_id='" + account_id + "'"
    return dbm.update(sql)

def update_job_config(job_id,robot_api, job_config, robot_template_str):
    job_config = job_config.replace("\n", "\\n")
    job_config = job_config.replace("\'", "\\'")
    job_config = job_config.replace('\"', '\\"')
    return dbm.update(sql_dict['update_job_config'].format(robot_api, job_config, robot_template_str, job_id))


def only_update_job_conifg_db(job_id, job_config):
    job_config = job_config.replace("\n", "\\n")
    job_config = job_config.replace("\'", "\\'")
    job_config = job_config.replace('\"', '\\"')
    return dbm.update(sql_dict['only_update_job_config'].format(job_config, job_id))