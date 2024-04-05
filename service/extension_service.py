from dao.contact_bank_dao import new_contact, new_extension_user, query_user_credit, query_user_already_contacts, update_user_credit, update_user_already_contacts, query_contact_by_profile
from tools.contactout_tools import get_contactout
from utils.extension_utils import process_profile, id_from_profile
import json

from utils.log import get_logger
from utils.config import config as config

logger = get_logger(config['log']['extension_log_file'])

def register_user(user_email, credit=0):
    return new_extension_user(user_email=user_email, credit=credit)

def fetch_user_credit(user_id):
    return query_user_credit(user_id=user_id)

def user_fetch_personal_email(user_id, linkedin_profile):
    logger.info(f'extension user {user_id} need personal email {linkedin_profile}')
    price = config['extension']['price']['email']
    credit = fetch_user_credit(user_id=user_id)
    if credit < price:
        logger.info(f'extension user {user_id} credit {credit} insufficient for fetch personal email, which need {price}')
        return None,  f"credit insufficient"
    need_update_credit = True

    already_contacts = query_user_already_contacts(user_id=user_id)
    if already_contacts is None:
        already_contacts = []
    else:
        already_contacts = json.loads(already_contacts)
    need_update_already_contacts = True

    profile = process_profile(linkedin_profile)
    lid = id_from_profile(profile)
    res = query_contact_by_profile(profile)
    if len(res) == 0:
        logger.info(f'extension user {user_id} need personal email {profile}, db not found, need fetch from outside')
        ## no information in db, need query contactout
        has_email, email_status = get_contactout().email_status(profile=profile, is_work_email=False)
        if not has_email:
            logger.info(f'extension user {user_id} need personal email {profile}, outside not found')
            return None,  f"no email"
        res = get_contactout().fetch_email(profile=profile)
        res = res['personal_email']
        ## update db
        new_contact(linked_profile=profile, linkedin_id=lid, name=lid, personal_email=res)
    else:
        logger.info(f'extension user {user_id} need personal email {profile}, will from db')
        for already_profile, contact_type in already_contacts:
            if already_profile == profile and 'personal_email'==contact_type:
                need_update_already_contacts = False
                need_update_credit = False
                logger.info(f'extension user {user_id} need personal email {profile}, already purchased, no need credit')
                break

        res = json.loads(res[0][2])

    if need_update_credit:
        new_credit = credit - price
        update_user_credit(user_id=user_id, new_credit=new_credit)

    if need_update_already_contacts:
        already_contacts.append((profile, 'personal_email'))
        update_user_already_contacts(user_id=user_id, new_already_contacts=already_contacts)

    return res, None