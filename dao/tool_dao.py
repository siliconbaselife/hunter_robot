from utils.db_manager import dbm
import uuid
from utils.config import config
from utils.log import get_logger
import json
import time

logger = get_logger(config['log']['log_file'])

sql_dict = {
    "get_undo_filter_task": "select id,manage_account_id, jd, resume_url from resume_filter_task where status=0",
    "update_filter_task_status": "update resume_filter_task set status={} where id={} ",
    "get_filter_task_by_manage_id": "select id, manage_account_id, resume_url, status, create_time,jd,filter_result,taskname from resume_filter_task where manage_account_id='{}'",
    "create_new_filter_task": "insert into resume_filter_task(manage_account_id, jd, resume_url,taskname) values ('{}', '{}', '{}','{}')",
    "update_filter_result": "update resume_filter_task set filter_result='{}', format_resumes = '{}' where id={}",
    "get_filter_task_by_id": "select id, manage_account_id, resume_url, status, create_time,jd,filter_result,taskname, format_resumes from resume_filter_task where id={}",
    "upload_online_profile": "insert into online_resume(manage_account_id, platform, raw_profile, candidate_id, name, company, age, race) values ('{}', '{}', '{}', '{}', '{}', '{}', {}, {})",
    "update_raw_profile": "update online_resume set raw_profile='{}', name = '{}', company = '{}', age = {}, race = {} where platform = '{}' and candidate_id='{}' and manage_account_id='{}'",
    "upload_online_profile_pdf": "insert into online_resume(manage_account_id, platform, cv_url, candidate_id) values ('{}', '{}', '{}', '{}')",
    "get_resume_by_candidate_id_and_platform": "select id,candidate_id,manage_account_id,platform,create_time from online_resume where candidate_id='{}' and platform='{}' and manage_account_id='{}'",
    "get_resume_by_candidate_ids_and_platform": "select candidate_id, raw_profile, cv_url from online_resume where candidate_id in {} and platform='{}' and manage_account_id='{}' order by id limit {}, {}",
    "get_resume_total_count_by_candidate_ids_and_platform": "select count(1) from online_resume where candidate_id in {} and platform='{}' and manage_account_id='{}'",
    "get_raw_latest_profile_by_candidate_id_and_platform": "select raw_profile from online_resume where candidate_id = '{}' and platform = '{}' order by id desc limit 1;",
    "get_resume_by_filter": "select id,candidate_id,manage_account_id,platform,create_time,raw_profile from online_resume where manage_account_id='{}' and platform='{}' and create_time > '{}' and create_time < '{}'",
    "get_resume_by_list": "select id,candidate_id,manage_account_id,platform,create_time,raw_profile from online_resume where manage_account_id='{}' and platform='{}' and create_time > '{}' and create_time < '{}' and list_name='{}'",
    "create_conversation_report": "insert into conversation_report (candidate_id, platform, contact, conversation) values ('{}', '{}', '{}', '{}')",
    "add_resume_list_db": "insert into resume_list(manage_account_id, platform, list_name) values ('{}', '{}', '{}')",
    "get_resume_list_db": "select list_name from resume_list where manage_account_id='{}' and platform='{}'",
    "add_list_relation": "insert into resume_list_relation(manage_account_id, list_name, candidate_id) values ('{}', '{}', '{}')",
    "save_config": "INSERT INTO plugin_chat_config (manage_account_id, platform, config_json) VALUES ('{}', '{}', '{}') ON DUPLICATE KEY UPDATE config_json = VALUES(config_json);",
    "create_profile_tag": "insert into user_profile_tag (manage_account_id, platform, tag) VALUES ('{}', '{}', '{}') ON DUPLICATE KEY UPDATE manage_account_id = VALUES(manage_account_id), platform = VALUES(platform), tag = VALUES(tag);",
    "query_profile_id_tag": "select id, tag from user_profile_tag where manage_account_id = '{}' and platform = '{}';",
    "delete_profile_tags": "delete from user_profile_tag where id in {};",
    "query_profile_tag_relation_by_user_and_candidate_db": "select tag_id, tag from user_profile_tag_relation where manage_account_id = '{}' and candidate_id = '{}' and platform = '{}';",
    "associate_profile_tag": "insert into user_profile_tag_relation (manage_account_id, candidate_id, platform, tag_id, tag) values ('{}', '{}', '{}', '{}', '{}') ON DUPLICATE KEY UPDATE manage_account_id = VALUES(manage_account_id), candidate_id = VALUES(candidate_id), platform = VALUES(platform), tag_id = VALUES(tag_id), tag = VALUES(tag);",
    "query_id_by_profile_tag_relation": "select id from user_profile_tag_relation where manage_account_id = '{}' and candidate_id = '{}' and platform = '{}' and tag in {};",
    "query_candidate_id_by_tag_relation": "select candidate_id from user_profile_tag_relation where manage_account_id = '{}' and platform = '{}' and tag in {};",
    "delete_profile_tag_relation": "delete from user_profile_tag_relation where manage_account_id = '{}' and candidate_id = '{}' and platform = '{}' and tag in {};",
    "create_customized_scenario_setting": "insert into customized_scenario_setting(manage_account_id, platform, context, scenario_info, extra_info) values('{}', '{}', '{}', '{}', '{}') ON DUPLICATE KEY UPDATE manage_account_id = VALUES(manage_account_id), platform = VALUES(platform), context = VALUES(context), scenario_info = VALUES(scenario_info), extra_info = VALUES(extra_info)",
    "update_customized_scenario_setting": "update customized_scenario_setting set scenario_info = '{}', extra_info = '{}' where id = '{}';",
    "query_customized_scenario_setting": "select scenario_info from customized_scenario_setting where manage_account_id = '{}' and platform = '{}' and context = '{}'",
    "query_customized_scenario_setting_with_id": "select id, scenario_info from customized_scenario_setting where manage_account_id = '{}' and platform = '{}' and context = '{}'",
    "query_customized_extra_setting": "select extra_info from customized_scenario_setting where manage_account_id = '{}' and platform = '{}' and context = '{}'",
    "query_email_info": "select email, pwd from email_credentials where manage_account_id = \'{}\';",
    "flush_email_credentials": "insert into email_credentials (manage_account_id, email, pwd, platform) values('{}', '{}', '{}', '{}') ON DUPLICATE KEY UPDATE manage_account_id = VALUES(manage_account_id), email = VALUES(email), pwd = VALUES(pwd), platform = VALUES(platform)",
    "get_email_credentials": "select manage_account_id, email, pwd, platform from email_credentials where manage_account_id = '{}' and platform = '{}';",
    "get_default_email_template_count": "select count(id) from default_email_template where platform = '{}';",
    "get_default_email_template_by_idx": "select template from default_email_template where platform = '{}' order by id limit {}, 1;",
    "get_default_inmail_template_count": "select count(id) from default_inmail_template where platform = '{}';",
    "get_default_inmail_template_by_idx": "select template from default_inmail_template where platform = '{}' order by id limit {}, 1;",
    "get_default_greeting_template_count": "select count(id) from default_greeting_template where platform = '{}';",
    "get_default_greeting_template_by_idx": "select template from default_greeting_template where platform = '{}' order by id limit {}, 1;",
    "get_all_default_greeting_template": "select template from default_greeting_template where platform = '{}' order by id asc",
    "create_customized_greeting": "insert into customized_greeting(manage_account_id, platform, scenario_info) VALUES('{}', '{}', '{}');",
    "update_customized_greeting": "update customized_greeting set scenario_info = '{}' where id = '{}'",
    "delete_customized_greeting": "delete from customized_greeting where id = '{}'",
    "query_customized_greeting": "select id, scenario_info from customized_greeting where manage_account_id = '{}' and platform = '{}'",
    'create_google_account': "insert into google_account (openid, manage_account_id, name, picture, google_account_email, credentials) values('{}', '{}', '{}', '{}', '{}', '{}') ON DUPLICATE KEY UPDATE openid = VALUES(openid), manage_account_id = VALUES(manage_account_id), name = VALUES(name), picture = VALUES(picture), google_account_email = VALUES(google_account_email), credentials = VALUES(credentials)",
    "query_google_account": "select openid, manage_account_id, name, picture, google_account_email, credentials from google_account where manage_account_id = '{}';",
    "get_google_account": "select openid, manage_account_id, name, picture, google_account_email, credentials from google_account where openid = '{}' and manage_account_id = '{}';",
    'delete_google_account': "delete from google_account where openid = '{}' and manage_account_id = '{}';",
}


def db_file_join(fields):
    file_str = '('
    for idx, field in enumerate(fields):
        file_str += '\''
        file_str += str(field)
        file_str += '\''
        if idx != len(fields) - 1:
            file_str += ','
    file_str += ')'
    return file_str


def save_plugin_chat_config(manage_account_id, platform, config_json):
    return dbm.insert(sql_dict['save_config'].format(manage_account_id, platform, config_json))


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
        return dbm.query(
            sql_dict['get_resume_by_list'].format(manage_account_id, platform, start_date, end_date, list_name))


def get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id):
    return dbm.query(
        sql_dict['get_resume_by_candidate_id_and_platform'].format(candidate_id, platform, manage_account_id))


def get_raw_latest_profile_by_candidate_id_and_platform(candidate_id, platform):
    return dbm.query(sql_dict['get_raw_latest_profile_by_candidate_id_and_platform'].format(candidate_id, platform))


def get_resume_by_candidate_ids_and_platform(manage_account_id, platform, candidate_ids, page, limit):
    return dbm.query(sql_dict['get_resume_by_candidate_ids_and_platform'].format(db_file_join(candidate_ids), platform,
                                                                                 manage_account_id, page, limit))


def get_resume_total_count_by_candidate_ids_and_platform(manage_account_id, platform, candidate_ids):
    return dbm.query(
        sql_dict['get_resume_total_count_by_candidate_ids_and_platform'].format(db_file_join(candidate_ids), platform,
                                                                                manage_account_id))[0][0]


def upload_profile_status_dao(manage_account_id, candidate_id, platform, status):
    sql = f"update online_resume set status = '{status}' where manage_account_id = '{manage_account_id}' and candidate_id='{candidate_id}' and platform = '{platform}'"
    return dbm.insert(sql)


def query_profile_status_dao(manage_account_id, candidate_id, platform):
    sql = f"select status from online_resume where manage_account_id = '{manage_account_id}' and candidate_id = '{candidate_id}' and platform = '{platform}'"
    data = dbm.query(sql)
    if len(data) == 0:
        return None

    return data[0][0]


def upload_online_profile(manage_account_id, platform, raw_profile, candidate_id, name, company, age, isChinese):
    raw_profile = raw_profile.replace("\n", "\\n")
    raw_profile = raw_profile.replace("\'", "\\'")
    raw_profile = raw_profile.replace('\"', '\\"')
    name.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')
    company = company.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')

    age = -1 if age is None else age
    race = 1 if isChinese else 2

    if len(get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id)) > 0:
        b1 = time.time()
        sql = sql_dict['update_raw_profile'].format(raw_profile, name, company, age, race, platform, candidate_id,
                                                    manage_account_id)
        logger.info(f"upload_online_profile update_raw_profile => sql: {sql}")
        dbm.update(sql)
        logger.info(
            f"update_raw_profile time: {time.time() - b1} sql: {sql}")

        return
    else:
        insert_sql = sql_dict['upload_online_profile'].format(manage_account_id, platform, raw_profile, candidate_id,
                                                              name,
                                                              company, age, race)
        dbm.insert(insert_sql)
        logger.info(f"upload_online_profile upload_online_profile => sql: {insert_sql}")
        b1 = time.time()
        sql = sql_dict['update_raw_profile'].format(raw_profile, name, company, age, race, platform, candidate_id,
                                                    manage_account_id)
        logger.info(f"upload_online_profile update_raw_profile => sql: {insert_sql}")
        dbm.update(sql)
        logger.info(
            f"update_raw_profile time: {time.time() - b1} sql: {sql}")
        return


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
    return dbm.insert(sql_dict['create_new_filter_task'].format(manage_account_id, jd, resume_url, taskname))


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
    return dbm.insert(
        sql_dict['create_conversation_report'].format(candidate_id, platform, contact_str, conversations_str))


def create_profile_tag_db(manage_account_id, platform, tag):
    return dbm.insert(sql_dict['create_profile_tag'].format(manage_account_id, platform, tag))


def query_profile_id_tag(manage_account_id, platform):
    return dbm.query(sql_dict['query_profile_id_tag'].format(manage_account_id, platform))


def query_profile_tag_relation_by_user_and_candidate_db(manage_account_id, candidate_id, platform):
    return dbm.query(
        sql_dict['query_profile_tag_relation_by_user_and_candidate_db'].format(manage_account_id, candidate_id,
                                                                               platform))


def associate_profile_tag(manage_account_id, candidate_id, platform, tag_id, tag):
    return dbm.query(sql_dict['associate_profile_tag'].format(manage_account_id, candidate_id, platform, tag_id, tag))


def query_id_by_profile_tag_relation(manage_account_id, candidate_id, platform, tags):
    return dbm.query(sql_dict['query_id_by_profile_tag_relation'].format(manage_account_id, candidate_id, platform,
                                                                         db_file_join(tags)))


def query_candidate_id_by_tag_relation(manage_account_id, platform, tags):
    rows = dbm.query(
        sql_dict['query_candidate_id_by_tag_relation'].format(manage_account_id, platform, db_file_join(tags)))
    return [row[0] for row in rows]


def delete_profile_tag_relation(manage_account_id, candidate_id, platform, tags):
    return dbm.query(
        sql_dict['delete_profile_tag_relation'].format(manage_account_id, candidate_id, platform, db_file_join(tags)))


def delete_profile_tags_db(ids):
    return dbm.query(sql_dict['delete_profile_tags'].format(db_file_join(ids)))


def create_customized_scenario_setting(manage_account_id, platform, context, scenario_info, extra_info=''):
    scenario_info = json.dumps(scenario_info, ensure_ascii=False)
    scenario_info = scenario_info.replace("\n", "\\n")
    scenario_info = scenario_info.replace("\'", "\\'")
    scenario_info = scenario_info.replace('\"', '\\"')

    extra_info = json.dumps(extra_info, ensure_ascii=False)
    extra_info = extra_info.replace("\n", "\\n")
    extra_info = extra_info.replace("\'", "\\'")
    extra_info = extra_info.replace('\"', '\\"')
    return dbm.query(
        sql_dict['create_customized_scenario_setting'].format(manage_account_id, platform, context, scenario_info,
                                                              extra_info))


def update_customized_scenario_setting(rid, scenario_info, extra_info):
    scenario_info = json.dumps(scenario_info, ensure_ascii=False)
    scenario_info = scenario_info.replace("\n", "\\n")
    scenario_info = scenario_info.replace("\'", "\\'")
    scenario_info = scenario_info.replace('\"', '\\"')

    extra_info = json.dumps(extra_info, ensure_ascii=False)
    extra_info = extra_info.replace("\n", "\\n")
    extra_info = extra_info.replace("\'", "\\'")
    extra_info = extra_info.replace('\"', '\\"')
    return dbm.query(
        sql_dict['update_customized_scenario_setting'].format(scenario_info, extra_info, rid))


def query_customized_scenario_setting(manage_account_id, platform, context):
    return dbm.query(sql_dict['query_customized_scenario_setting'].format(manage_account_id, platform, context))


def query_customized_scenario_setting_with_id(manage_account_id, platform, context):
    return dbm.query(sql_dict['query_customized_scenario_setting_with_id'].format(manage_account_id, platform, context))


def query_customized_extra_setting(manage_account_id, platform, context):
    return dbm.query(sql_dict['query_customized_extra_setting'].format(manage_account_id, platform, context))


def query_email_info(manage_account_id):
    return dbm.query(sql_dict['query_email_info'].format(manage_account_id))


def flush_email_credentials_db(manage_account_id, email, pwd, platform):
    return dbm.insert(sql_dict['flush_email_credentials'].format(manage_account_id, email, pwd, platform))


def get_email_credentials_db(manage_account_id, platform):
    return dbm.query(sql_dict['get_email_credentials'].format(manage_account_id, platform))


def get_default_email_template_count(platform):
    return dbm.query(sql_dict['get_default_email_template_count'].format(platform))


def get_default_email_template_by_idx(platform, idx):
    return dbm.query(sql_dict['get_default_email_template_by_idx'].format(platform, idx))


def get_default_inmail_template_count(platform):
    return dbm.query(sql_dict['get_default_email_template_count'].format(platform))


def get_default_inmail_template_by_idx(platform, idx):
    return dbm.query(sql_dict['get_default_email_template_by_idx'].format(platform, idx))


def get_default_greeting_template_count(platform):
    return dbm.query(sql_dict['get_default_greeting_template_count'].format(platform))


def get_default_greeting_template_by_idx(platform, idx):
    return dbm.query(sql_dict['get_default_greeting_template_by_idx'].format(platform, idx))


def get_all_default_greeting_template(platform):
    return dbm.query(sql_dict['get_all_default_greeting_template'].format(platform))


def query_tag_flow_status(manage_account_id, platform, tag):
    sql = f"select candidate_id, flow_status from user_profile_tag_relation where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}'"
    data = dbm.query(sql)
    return data


def update_flow_status(manage_account_id, platform, tag, candidate_id, flow_status):
    update_sql = f"update user_profile_tag_relation set flow_status ='{flow_status}' where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}' and candidate_id = '{candidate_id}'"
    dbm.update(update_sql)


def fetch_tag_log(manage_account_id, platform, tag, candidate_id):
    sql = f"select log from user_profile_tag_relation where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}' and candidate_id = '{candidate_id}'"
    logger.info(f'fetch_tag_log sql: {sql}')
    data = dbm.query(sql)
    if len(data) > 0:
        logs = data[0][0].replace('\n', '\\n')
        return json.loads(logs)
    else:
        return []


# def fetch_tag_logs(manage_account_id, platform, tag, candidate_ids):
#     candidate_ids_list = ["'" + candidate_id + "'" for candidate_id in candidate_ids]
#     candidate_ids_str = ", ".join(candidate_ids_list)
#     sql = f"select , log from user_profile_tag_relation where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}' and candidate_id in ({candidate_ids_str})"
#     logger.info(f'fetch_tag_logs sql: {sql}')
#     data = dbm.query(sql)
#     if len(data) > 0:
#         logs_list = []
#         for d in data:
#
#         return logs_list
#     else:
#         return []


def update_tag_log(manage_account_id, platform, tag, candidate_id, log):
    update_sql = f"update user_profile_tag_relation set log = '{log}' where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}' and candidate_id = '{candidate_id}'"
    logger.info(f"update_tag_log => {update_sql}")
    dbm.update(update_sql)


def query_tag_resume_infos(manage_account_id, platform, tag):
    sql = f"select a.company, a.status FROM online_resume a where manage_account_id = '{manage_account_id}' and platform = '{platform}' and candidate_id in (SELECT candidate_id FROM user_profile_tag_relation WHERE manage_account_id = '{manage_account_id}' and tag = '{tag}')"
    data = dbm.query(sql)
    return data


def query_stage_by_id(manage_account_id, platform, tag, candidate_id):
    sql = f"select flow_status from user_profile_tag_relation where manage_account_id = '{manage_account_id}' and platform = '{platform}' and tag = '{tag}' and candidate_id = '{candidate_id}'"
    data = dbm.query(sql)
    if len(data) == 0:
        return ""
    else:
        return data[0][0]


def query_tag_filter_num(manage_account_id, platform, tag, company, candidate_name):
    sql = f"select count(*) from online_resume a where manage_account_id = '{manage_account_id}' and platform = '{platform}'"
    if company is not None and len(company) > 0:
        sql += f" and company = '{company}'"
    if candidate_name is not None and len(candidate_name) > 0:
        sql += f" and name = '{candidate_name}'"
    sql += f" and candidate_id in (select candidate_id from user_profile_tag_relation WHERE manage_account_id = '{manage_account_id}' and tag = '{tag}')"

    data = dbm.query(sql)
    return data[0][0]


def query_tag_filter_profiles(manage_account_id, platform, tag, company, candidate_name, page, limit):
    sql = f"select candidate_id, raw_profile, cv_url, status from online_resume a where manage_account_id = '{manage_account_id}' and platform = '{platform}'"
    if company is not None and len(company) > 0:
        sql += f" and company = '{company}'"
    if candidate_name is not None and len(candidate_name) > 0:
        sql += f" and name like '%{candidate_name}%'"
    sql += f" and candidate_id in (select candidate_id from user_profile_tag_relation WHERE manage_account_id = '{manage_account_id}' and tag = '{tag}') limit {page}, {limit}"

    logger.info(f"query_tag_filter_profiles: {sql}")
    data = dbm.query(sql)
    return data


def query_tag_filter_num_new(manage_account_id, platform, tag, company, candidate_name, stage, status):
    sql = f"select count(*) from user_profile_tag_relation a inner join online_resume b on a.manage_account_id = b.manage_account_id and a.candidate_id = b.candidate_id where a.manage_account_id = '{manage_account_id}' and a.platform = '{platform}' and a.tag = '{tag}'"
    if company is not None and len(company) > 0:
        sql += f" and b.company = '{company}' "
    if candidate_name is not None and len(candidate_name) > 0:
        sql += f" and b.name like '%{candidate_name}%'"
    if stage is not None and len(stage) > 0:
        sql += f" and a.flow_status = '{stage}'"
    if status is not None and len(status) > 0:
        sql += f" and b.status = '{status}'"

    s = time.time()
    data = dbm.query(sql)
    e = time.time()
    logger.info(f"query_tag_filter_num_new: {sql} time: {e - s}")
    return data[0][0]


def query_tag_filter_profiles_new(manage_account_id, platform, tag, company, candidate_name, stage, status, min_age, max_age, race, page,
                                  limit):
    sql = f"select a.candidate_id, b.raw_profile, b.cv_url, b.status, a.flow_status, a.log from user_profile_tag_relation a inner join online_resume b on a.manage_account_id = b.manage_account_id and a.candidate_id = b.candidate_id where a.manage_account_id = '{manage_account_id}' and a.platform = '{platform}' and a.tag = '{tag}'"
    if company is not None and len(company) > 0:
        sql += f" and b.company = '{company}' "
    if candidate_name is not None and len(candidate_name) > 0:
        sql += f" and b.name like '%{candidate_name}%'"
    if stage is not None and len(stage) > 0:
        sql += f" and a.flow_status = '{stage}'"
    if status is not None and len(status) > 0:
        sql += f" and b.status = '{status}'"
    if race is not None:
        sql += f" and b.race = {race}"
    if min_age is not None and max_age is not None:
        sql += f" and b.age >= {min_age} and b.age <= {max_age}"

    sql += f" limit {page}, {limit}"

    s = time.time()
    data = dbm.query(sql)
    e = time.time()
    logger.info(f"query_tag_filter_profiles_new: {sql} time: {e - s}")
    return data


def create_customized_greeting(manage_account_id, platform, scenario_info):
    scenario_info = scenario_info.replace("\n", "\\n")
    scenario_info = scenario_info.replace("\'", "\\'")
    scenario_info = scenario_info.replace('\"', '\\"')
    return dbm.query(sql_dict['create_customized_greeting'].format(manage_account_id, platform, scenario_info))


def update_customized_greeting(scenario_info, rid):
    scenario_info = scenario_info.replace("\n", "\\n")
    scenario_info = scenario_info.replace("\'", "\\'")
    scenario_info = scenario_info.replace('\"', '\\"')
    return dbm.query(sql_dict['update_customized_greeting'].format(scenario_info, rid))


def delete_customized_greeting(rid):
    return dbm.query(sql_dict['delete_customized_greeting'].format(rid))


def query_customized_greeting(manage_account_id, platform):
    return dbm.query(sql_dict['query_customized_greeting'].format(manage_account_id, platform))


def query_google_account(manage_account_id):
    return dbm.query(sql_dict['query_google_account'].format(manage_account_id))


def get_google_account(openid, manage_account_id):
    return dbm.query(sql_dict['get_google_account'].format(openid, manage_account_id))


def delete_google_account(openid, manage_account_id):
    return dbm.query(sql_dict['delete_google_account'].format(openid, manage_account_id))


def create_google_account(openid, manage_account_id, name, picture, google_account_email, credentials):
    return dbm.insert(
        sql_dict['create_google_account'].format(openid, manage_account_id, name, picture, google_account_email,
                                                 credentials))


def update_profile_age_and_race(manage_account_id, candidate_id, platform, age, isChinese):
    age = -1 if age is None else age
    race = 1 if isChinese else 2
    sql = f"update online_resume set age = {age}, race = {race} where platform = '{platform}' and candidate_id='{candidate_id}' and manage_account_id='{manage_account_id}'"
    dbm.update(sql)


def query_letter_profile(id):
    sql = f"select id, candidate_id, manage_account_id, raw_profile from online_resume where id > '{id}' and platform = 'Linkedin' limit 0, 10"
    rows = dbm.query(sql)
    return rows
