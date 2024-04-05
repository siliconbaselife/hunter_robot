from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.db_manager import dbm
import shortuuid
import json

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "new_extension_user": "insert into extension_user(user_id, user_credit, user_email, already_contacts) values ('{}', {}, '{}', '{}')",
    "query_user_credit": "select user_credit from extension_user where user_id='{}'",
    "update_user_credit": "update extension_user set user_credit={} where user_id='{}'",
    "query_user_already_contacts": "select already_contacts from extension_user where user_id='{}'",
    "update_user_already_contacts": "update extension_user set already_contacts='{}' where user_id='{}'",

    "new_contact": "insert into contact_bank(linkedin_profile, linkedin_id, name, personal_email, work_email, work_email_status, phone) values ('{}', '{}', '{}', '{}', '{}', '{}', '{}')",
    "update_contact_personal_email": "update contact_bank set personal_email = '{}' where linkedin_profile = '{}'",
    "query_contact_by_profile": "select linkedin_id, name, personal_email, work_email, work_email_status, phone from contact_bank where linkedin_profile='{}'",
}

def new_extension_user(user_email, credit=0):
    user_id = shortuuid.uuid()
    dbm.insert(sql_dict['new_extension_user'].format(user_id, credit, user_email, []))
    return user_id

def update_user_credit(user_id, new_credit):
    dbm.update(sql_dict['update_user_credit'].format(new_credit, user_id))

def update_user_already_contacts(user_id, new_already_contacts):
    dbm.update(sql_dict['update_user_already_contacts'].format(json.dumps(new_already_contacts), user_id))

def query_user_credit(user_id):
    return dbm.query(sql_dict['query_user_credit'].format(user_id))[0][0]

def query_user_already_contacts(user_id):
    return dbm.query(sql_dict['query_user_already_contacts'].format(user_id))[0][0]

def new_contact(linked_profile, linkedin_id, name, personal_email=[], work_email=[], work_email_status=[], phone=[]):
    dbm.insert(sql_dict['new_contact'].format(linked_profile, linkedin_id, name, json.dumps(personal_email), json.dumps(work_email), json.dumps(work_email_status), json.dumps(phone)))

def query_contact_by_profile(linkedin_profile):
    return dbm.query(sql_dict['query_contact_by_profile'].format(linkedin_profile))
