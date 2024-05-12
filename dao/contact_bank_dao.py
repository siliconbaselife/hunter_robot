from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.db_manager import dbm
import shortuuid
import json

logger = get_logger(config['log']['log_file'])
sql_dict = {
    "new_extension_user": "insert into extension_user(user_id, user_credit, already_contacts) values ('{}', {}, '{}')",
    "query_user_credit": "select user_credit from extension_user_credit where user_id='{}'",
    "update_user_credit": "update extension_user_credit set user_credit={} where user_id='{}'",
    "query_extension_user_link": "select * from extension_user_link where user_id='{}' and link_linkedin_id='{}' and link_contact_type='{}'",
    "insert_extension_user_link": "insert into extension_user_link(user_id, link_linkedin_id, link_contact_type) values ('{}', '{}', '{}')",
    "new_contact": "insert into contact_bank(linkedin_profile, linkedin_id, name, personal_email, work_email, work_email_status, phone) values ('{}', '{}', '{}', '{}', '{}', '{}', '{}')",
    "update_contact_personal_email": "update contact_bank set personal_email = '{}' where linkedin_id = '{}'",
    "update_contact_phone": "update contact_bank set phone = '{}' where linkedin_id = '{}'",
    "query_contact_by_profile": "select linkedin_id, name, personal_email, work_email, work_email_status, phone from contact_bank where linkedin_profile='{}'",
}


def new_extension_user(user_id, credit=0):
    dbm.insert(sql_dict['new_extension_user'].format(user_id, credit, []))


def update_user_credit(user_id, new_credit):
    dbm.update(sql_dict['update_user_credit'].format(new_credit, user_id))


def query_user_credit(user_id):
    return dbm.query(sql_dict['query_user_credit'].format(user_id))


def query_extension_user_link(user_id, linkedin_id, contact_type):
    return dbm.query(sql_dict['query_extension_user_link'].format(user_id, linkedin_id, contact_type))


def insert_extension_user_link(user_id, linkedin_id, contact_type):
    dbm.update(sql_dict['insert_extension_user_link'].format(user_id, linkedin_id, contact_type))


def new_contact(linked_profile, linkedin_id, name, personal_email=[], work_email=[], work_email_status=[], phone=[]):
    dbm.insert(sql_dict['new_contact'].format(linked_profile, linkedin_id, name, json.dumps(personal_email),
                                              json.dumps(work_email), json.dumps(work_email_status), json.dumps(phone)))


def update_contact_personal_email(linkedin_id, personal_emails):
    dbm.update(sql_dict['update_contact_personal_email'].format(json.dumps(personal_emails), linkedin_id))


def update_contact_phone(linkedin_id, phones):
    dbm.update(sql_dict['update_contact_phone'].format(json.dumps(phones), linkedin_id))


def query_contact_by_profile(linkedin_profile):
    return dbm.query(sql_dict['query_contact_by_profile'].format(linkedin_profile))


def query_contact_by_profile_id(linkedin_id):
    data = dbm.query(
        f"select linkedin_id, name, personal_email, work_email, work_email_status, phone from contact_bank where linkedin_id='{linkedin_id}'")

    if len(data) == 0:
        return None

    person_emails = json.loads(data[0][2])
    phones = json.loads(data[0][5])

    return person_emails, phones
