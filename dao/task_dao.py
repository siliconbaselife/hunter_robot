from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.utils import deal_json_invaild
import json

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "register_job": "insert into job(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config, share, manage_account_id,robot_template) values ('{}','{}','{}','{}','{}','{}','{}', {}, '{}','{}')",
    "query_job_id": "select job_id from job where platform_type = '{}' and platform_id= '{}'",
    # "query_job_requirement": "select requirement_config from job where job_id = {}",
    "query_job_robotapi": "select robot_api from job where job_id='{}'",
    "register_account": "insert into account(account_id, platform_type, platform_id, jobs, task_config, description, manage_account_id,ver) values ('{}','{}','{}','{}','{}','{}','{}','{}')",
    "query_account_id": "select account_id from account where platform_type='{}' and platform_id='{}'",
    "query_account_type": "select platform_type from account where account_id='{}'",
    "get_jobs": "select jobs from account where account_id='{}'",
    "get_task": "select task_config from account where account_id='{}'",
    "new_candidate": "insert into candidate(candidate_id, candidate_name, age, degree, location, position, details) values ('{}','{}','{}','{}','{}','{}','{}')",
    "update_candidate_contact": "update candidate set contact='{}' where candidate_id='{}'",
    "query_candidate": "select candidate_id, candidate_name, age, degree, location, position, contact, details, filter_result from candidate where candidate_id='{}'",
    "query_chat_details": "select source, details, contact from chat where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "new_chat": "insert into chat(account_id, job_id, candidate_id, candidate_name, source, status, details, filter_result) values ('{}','{}','{}','{}','{}','{}','{}','{}')",
    "update_chat": "update chat set source='{}', status='{}', details='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "update_chat_only_details": "update chat set details='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "update_chat_contact": "update chat set contact='{}' where account_id='{}' and job_id='{}' and candidate_id='{}'",
    "query_candidate_already_chat": "select status, source from chat where job_id='{}' and candidate_id='{}'",
    "add_task_count": "update account_exec_log set hello_sum_exec = hello_sum_exec+{} where account_id='{}' and job_id='{}' and exec_date='{}'",
    "insert_sub_task_log": "insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ('{}','{}','{}','{}')",
    "get_account_task_log": "select id, account_id, job_id, exec_date, hello_sum_need,hello_sum_exec,create_time, update_time from account_exec_log where account_id='{}' and exec_date='{}'",
    "get_job_task_log": "select id, account_id, job_id, exec_date, hello_sum_need,hello_sum_exec,create_time, update_time from account_exec_log where account_id='{}' and exec_date='{}'",
    "get_job_by_id": "select job_id,platform_type,platform_id,job_name,job_jd,robot_api,job_config,create_time,update_time,share,robot_api,manage_account_id,robot_template from job where job_id='{}'",
    "get_chats_by_job_id_with_start": "select account_id, job_id, candidate_id, candidate_name, source, status, contact, details, filter_result, create_time, update_time from chat where job_id='{}' order by update_time desc limit {},{}",
    "get_chats_by_job_id_with_date": "select account_id, job_id, candidate_id, candidate_name, source, status, contact, details, filter_result, create_time, update_time from chat where job_id='{}' and create_time>'{}' and create_time<'{}' order by create_time desc",
    "get_chats_num_by_job_id": "select count(1) from chat where job_id='{}' and contact!='NULL'",
    "get_chats_by_ids": "select candidate_id, candidate_name, contact, details, filter_result, update_time, recall_cnt, job_id from chat where account_id='{}' and candidate_id in {} order by update_time desc",
    "recall_exec": "update chat set recall_cnt = recall_cnt + 1 where account_id='{}' and candidate_id='{}'",
    "add_friend_report": "update chat set added_friend=1 where account_id='{}' and candidate_id='{}'",
    "get_job_id_in_chat": "select job_id from chat where account_id='{}' and candidate_id='{}' order by create_time desc limit 1",
    "get_robot_template_by_job_id": "select robot_template from job where job_id='{}'",
    "get_independent_by_account_id": "select independent from account where account_id='{}'",
    "get_one_time_task_by_account_id": "select id,task_config from one_time_task where account_id='{}' and status = 0",
    "get_one_time_task_list": "select id,task_config,status from one_time_task where account_id='{}'",
    "update_one_time_status_by_id": "update one_time_task set status={} where id={}",
    "new_one_time_task": "insert into one_time_task(account_id, task_config) values ('{}', '{}')",
    "has_contact": "select contact from chat where candidate_id='{}' and account_id='{}'",
    "insert_filter_cache": "insert into candidate_filter_cache(candidate_id, job_id, prompt,filter_result) values ('{}','{}','{}','{}')",
    "get_filter_cache": "select candidate_id, job_id, prompt, filter_result from candidate_filter_cache where candidate_id='{}' and job_id='{}'",
    "update_filter_cache": "update candidate_filter_cache set prompt='{}',filter_result='{}' where candidate_id='{}' and job_id='{}'",
    "delete_account_by_id":"delete from account where account_id='{}'"
}


def get_template_id(job_id):
    sql = f"select robot_template from job where job_id='{job_id}'"
    return dbm.query(sql)


def update_status_infos(candidate_id, account_id, status_infos):
    sql = f"update chat set status_infos = '{status_infos}' where candidate_id = '{candidate_id}' and account_id = '{account_id}'"
    dbm.update(sql)


def query_template_config(template_id):
    sql = f"select template_config from llm_template where template_id = '{template_id}'"
    return dbm.query(sql)


def query_status_infos(candidate_id, account_id):
    sql = f"select status_infos from chat where candidate_id = '{candidate_id}' and account_id = '{account_id}'"
    return dbm.query(sql)


def insert_filter_cache(candidate_id, job_id, prompt, filter_result):
    prompt = prompt.replace("\n", "\\n")
    prompt = prompt.replace('\"', '\\"')
    prompt = prompt.replace("\'", "\\'")
    filter_result = filter_result.replace("\n", ";")
    return dbm.insert(sql_dict['insert_filter_cache'].format(candidate_id, job_id, prompt, filter_result))


def get_filter_cache(candidate_id, job_id):
    return dbm.query(sql_dict['get_filter_cache'].format(candidate_id, job_id))


def update_filter_cache(prompt, filter_result, candidate_id, job_id):
    prompt = prompt.replace("\n", "\\n")
    prompt = prompt.replace('\"', '\\"')
    prompt = prompt.replace("\'", "\\'")
    filter_result = filter_result.replace("\n", ";")
    return dbm.update(sql_dict['update_filter_cache'].format(prompt, filter_result, candidate_id, job_id))


def has_contact_db(candidate_id, account_id):
    ret = dbm.query(sql_dict['has_contact'].format(candidate_id, account_id))
    if len(ret) == 0:
        logger.info(f"chat_error_{account_id}, {candidate_id}")
        return False
    flag = False
    for r in ret:
        if r[0] != None and r[0] != 'NULL' and r[0] != '':
            flag = True
    return flag


def get_one_time_task_list_db(account_id):
    return dbm.query(sql_dict['get_one_time_task_list'].format(account_id))


def new_one_time_task_db(account_id, one_time_task_config):
    one_time_task_config_j = json.dumps(one_time_task_config, ensure_ascii=False)
    one_time_task_config_j = one_time_task_config_j.replace("\'", "\\'")
    one_time_task_config_j = one_time_task_config_j.replace('\"', '\\"')
    one_time_task_config_j = one_time_task_config_j.replace('\\n', ';')
    one_time_task_config_j = one_time_task_config_j.replace('\n', ';')
    return dbm.insert(sql_dict["new_one_time_task"].format(account_id, one_time_task_config_j))


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


def register_job_db(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config, share,
                    manage_account_id, robot_template):
    if share == None:
        share = 0
    dbm.insert(
        sql_dict['register_job'].format(job_id, platform_type, platform_id, job_name, job_jd, robot_api, job_config,
                                        share, manage_account_id, robot_template))
    return job_id


# def query_job_requirement_db(job_id):
#     return dbm.query(sql_dict['query_job_requirement'].format(job_id))

def query_job_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_job_id'].format(platform_type, platform_id))[0][0]


def query_robotapi_db(job_id):
    return dbm.query(sql_dict['query_job_robotapi'].format(job_id))[0][0]


def register_account_db(account_id, platform_type, platform_id, jobs, task_config, desc, manage_account_id):
    return dbm.insert(sql_dict['register_account'].format(account_id, platform_type, platform_id, jobs, task_config, desc,
                                                   manage_account_id, 'v1'))

def delete_account_by_id(account_id):
    return dbm.delete(sql_dict['delete_account_by_id'].format(account_id))

def register_account_db_v2(account_id, platform_type, platform_id, jobs, task_config, account_name, manage_account_id, ver):
    return dbm.insert(sql_dict['register_account'].format(account_id, platform_type, platform_id, jobs, task_config, account_name,
                                                   manage_account_id, ver))

def query_account_id_db(platform_type, platform_id):
    return dbm.query(sql_dict['query_account_id'].format(platform_type, platform_id))[0][0]


def query_account_type_db(account_id):
    return dbm.query(sql_dict['query_account_type'].format(account_id))[0][0]


def new_candidate_db(candidate_id, candidate_name, age, degree, location, position, details):
    location = location.replace("\'", "\\'")
    location = location.replace('\"', '\\"')
    location = location.replace('\n', '.')
    details = details.replace("\'", "\\'")
    details = details.replace('\"', '\\"')
    details = details.replace('\n', '.')
    position = position.replace("\'", "\\'")
    position = position.replace('\"', '\\"')
    position = position.replace('\n', '.')
    # degree = degree.replace("\'", "\\'")
    # degree = degree.replace('\"', '\\"')
    try:
        s = sql_dict['new_candidate'].format(candidate_id, candidate_name, age, degree, location, position, details)
        dbm.insert(s)
    except BaseException as e:
        logger.info(f'new_candidate_error, (msg: {details})')


def query_candidate_exist(candidate_id):
    return len(dbm.query(sql_dict['query_candidate'].format(candidate_id))) > 0


def query_candidate_name_and_filter_result(candidate_id):
    ret = dbm.query(sql_dict['query_candidate'].format(candidate_id))
    if len(ret) == 0:
        logger.info(f'report_without_filter, {candidate_id}')
    item = ret[0]
    return item[1], item[8]


def query_candidate_by_id(candidate_id):
    return dbm.query(sql_dict['query_candidate'].format(candidate_id))


def update_candidate_contact_db(candidate_id, contact):
    dbm.update(sql_dict['update_candidate_contact'].format(contact, candidate_id))


def new_chat_db(account_id, job_id, candidate_id, candidate_name, source=None, status='init', details=None,
                filter_result=None):
    if details is not None:
        details = details.replace("\'", "\\'")
        details = details.replace('\"', '\\"')
    dbm.insert(sql_dict['new_chat'].format(account_id, job_id, candidate_id, candidate_name, source, status, details,
                                           filter_result))


def query_chat_db(account_id, job_id, candidate_id):
    return dbm.query(sql_dict['query_chat_details'].format(account_id, job_id, candidate_id))


def update_chat_db(account_id, job_id, candidate_id, source, status, details):
    details = details.replace("\'", "\\'")
    details = details.replace('\"', '\\"')
    dbm.update(sql_dict['update_chat'].format(source, status, details, account_id, job_id, candidate_id))


def update_chat_only_details_db(account_id, job_id, candidate_id, details):
    details = details.replace("\'", "\\'")
    details = details.replace('\"', '\\"')
    dbm.update(sql_dict['update_chat_only_details'].format(details, account_id, job_id, candidate_id))


def update_chat_contact_db(account_id, job_id, candidate_id, contact):
    dbm.update(sql_dict['update_chat_contact'].format(contact, account_id, job_id, candidate_id))


def is_chatting_db(job_id, candidate_id):
    ret = dbm.query(sql_dict['query_candidate_already_chat'].format(job_id, candidate_id))
    return len(ret) > 0


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
    ret = dbm.query(sql_dict["get_job_by_id"].format(job_id))
    new_ret = []
    for r in ret:
        s = r[6].replace('\n', '\\n')
        new_ret.append([r[0], r[1], r[2], r[3], r[4], r[5], s, r[7], r[8], r[9], r[10],r[11], r[12]])
    return new_ret


def get_chats_by_job_id_with_start(job_id, start, limit):
    return dbm.query(sql_dict["get_chats_by_job_id_with_start"].format(job_id, start, limit))

def get_chats_by_job_id_with_date(job_id, start_date, end_date):
    return dbm.query(sql_dict["get_chats_by_job_id_with_date"].format(job_id, start_date, end_date))


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


if __name__ == "__main__":
    judge_result = {
        'judge': True,
        'details': '12312321\n213213'
    }
    filter_result = json.dumps(judge_result, ensure_ascii=False)
    candidate_id = '111'
    job_id = 'jjj'
    prompt = 'sdfsdf'
    insert_filter_cache(candidate_id, job_id, prompt, filter_result)
