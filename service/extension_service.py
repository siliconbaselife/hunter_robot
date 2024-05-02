from dao.contact_bank_dao import new_contact, new_extension_user, query_user_credit, query_user_already_contacts, \
    update_user_credit, update_user_already_contacts, query_contact_by_profile, update_contact_personal_email, \
    update_contact_phone
from tools.contactout_tools import get_contactout
from utils.extension_utils import process_profile, id_from_profile
import json
from functools import partial

from utils.log import get_logger
from utils.config import config as config

logger = get_logger(config['log']['extension_log_file'])


def register_user(user_email, credit=0):
    return new_extension_user(user_email=user_email, credit=credit)


def fetch_user_credit(user_id):
    return query_user_credit(user_id=user_id)


def user_fetch_personal_email(user_id, linkedin_profile):
    logger.info(f'extension user {user_id} need personal email {linkedin_profile}')
    price = config['extension']['price']['personal_email']
    credit = fetch_user_credit(user_id=user_id)
    if credit < price:
        logger.info(
            f'extension user {user_id} credit {credit} insufficient for fetch personal email, which need {price}')
        return None, f"credit insufficient"
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
            return None, f"no email"
        res = get_contactout().fetch_email(profile=profile)
        res = res['personal_email']
        ## update db
        new_contact(linked_profile=profile, linkedin_id=lid, name=lid, personal_email=res)
    else:
        logger.info(f'extension user {user_id} need personal email {profile}, will from db')
        for already_profile, contact_type in already_contacts:
            if already_profile == profile and 'personal_email' == contact_type:
                need_update_already_contacts = False
                need_update_credit = False
                logger.info(
                    f'extension user {user_id} need personal email {profile}, already purchased, no need credit')
                break

        res = json.loads(res[0][2])

    if need_update_credit:
        new_credit = credit - price
        update_user_credit(user_id=user_id, new_credit=new_credit)

    if need_update_already_contacts:
        already_contacts.append((profile, 'personal_email'))
        update_user_already_contacts(user_id=user_id, new_already_contacts=already_contacts)

    return res, None


def user_fetch_contact(user_id, linkedin_profile, contact_tag):
    ctx_map = {
        'personal_email': {
            'price': config['extension']['price']['personal_email'],
            'status_func': partial(get_contactout().email_status, is_work_email=False),
            'fetch_func': get_contactout().fetch_email,
            'update_db_func': update_contact_personal_email,
            'contactout_ret_field': 'personal_email',
            'contact_type': 'personal_email',
            'db_idx': 2,
        },
        'phone': {
            'price': config['extension']['price']['phone'],
            'status_func': get_contactout().phone_status,
            'fetch_func': get_contactout().fetch_phone,
            'update_db_func': update_contact_phone,
            'contactout_ret_field': 'phone',
            'contact_type': 'phone',
            'db_idx': 5,
        }
    }
    assert contact_tag in ctx_map, f"user_fetch_contact only support {set(ctx_map.keys())}, but got: {contact_tag}"
    ctx = ctx_map[contact_tag]
    logger.info(f'extension user {user_id} need contact({contact_tag}) for {linkedin_profile}')
    price = ctx['price']
    credit = fetch_user_credit(user_id=user_id)
    if credit < price:
        logger.info(
            f'extension user {user_id} credit {credit} insufficient for fetch {contact_tag}, which need {price}')
        return None, f"credit insufficient"
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
    db_item_exists = len(res) > 0
    db_content = json.loads(res[0][ctx['db_idx']]) if db_item_exists else None
    if not db_content:
        logger.info(
            f'extension user {user_id} need contact({contact_tag}) for {profile}, db not found, need fetch from outside')
        ## no information in db, need query contactout
        has_contact, _ = ctx['status_func'](profile=profile)
        if not has_contact:
            logger.info(f'extension user {user_id} need contact({contact_tag}) for {profile}, outside not found')
            return None, f"no contact for {contact_tag}"
        res = ctx['fetch_func'](profile=profile)
        res = res[ctx['contactout_ret_field']]

        ## update db
        if db_item_exists:
            logger.info(
                f'extension user {user_id} need contact({contact_tag}) for {profile}, got outside {res}, now will update contact')
            ctx['update_db_func'](profile, res)
        else:
            logger.info(
                f'extension user {user_id} need contact({contact_tag}) for {profile}, got outside {res}, now will new contact')
            new_contact(linked_profile=profile, linkedin_id=lid, name=lid, **{ctx['contact_type']: res})
    else:
        logger.info(f'extension user {user_id} need contact({contact_tag}) for {profile}, will from db')
        for already_profile, contact_type in already_contacts:
            if already_profile == profile and ctx['contact_type'] == contact_type:
                need_update_already_contacts = False
                need_update_credit = False
                logger.info(
                    f'extension user {user_id} need contact({contact_tag}) for {profile}, already purchased, no need credit')
                break
        res = db_content

    if need_update_credit:
        new_credit = credit - price
        update_user_credit(user_id=user_id, new_credit=new_credit)

    if need_update_already_contacts:
        already_contacts.append((profile, ctx['contact_type']))
        update_user_already_contacts(user_id=user_id, new_already_contacts=already_contacts)

    return res, None


def refresh_contact(manage_account_id, candidate_id, profile):
    contact_info = profile['profile']['contactInfo']
    personal_email = contact_info['Email']
    phone = contact_info['Phone']

    refresh_contact_db(candidate_id, personal_email, phone)
    refresh_person_contact_db(manage_account_id, candidate_id, personal_email, phone)


def refresh_contact_db(candidate_id, personal_email, phone):
    if personal_email is None and phone is None:
        return
    name = candidate_id.split('/')[-1]
    res = query_contact_by_profile(candidate_id)
    if len(res) > 0:
        origin_personal_emails = json.loads(res[0][2])
        origin_phones = json.loads(res[0][5])
        if personal_email not in origin_personal_emails:
            update_contact_personal_email(candidate_id, [personal_email])
        if phone not in origin_phones:
            update_contact_phone(candidate_id, [phone])
    else:
        new_contact(linked_profile=candidate_id, linkedin_id=name, name=name, personal_email=[personal_email],
                    phone=[phone])


def refresh_person_contact_db(manage_account_id, candidate_id, personal_email, phone):
    already_contacts = query_user_already_contacts(user_id=manage_account_id)
    if already_contacts is None:
        already_contacts = []
    else:
        already_contacts = json.loads(already_contacts)

    if personal_email is not None:
        pass

    if phone is not None:
        pass
