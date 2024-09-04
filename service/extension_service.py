from dao.contact_bank_dao import *
from tools.contactout_tools import get_contactout
from utils.extension_utils import process_profile, info_from_profile
import json
from functools import partial

from utils.log import get_logger
from utils.config import config as config

from threading import Lock

logger = get_logger(config['log']['extension_log_file'])

class PLM:
    def __init__(self):
        self._global_lock = Lock()
        self._profile_locks = {}

    def get_lock(self, profile):
        with self._global_lock:
            if profile not in self._profile_locks:
                self._profile_locks[profile] = Lock()
            logger.info(f"profile {profile} return lock")
            return self._profile_locks[profile]
_PLM = PLM()

def fetch_user_credit(user_id):
    res = query_user_credit(user_id=user_id)
    if len(res) == 0:
        return None
    return res[0][0]

def query_user_contact(user_id, linkedin_profile, contact_tag):
    profile = process_profile(linkedin_profile)
    name, lid = info_from_profile(profile)

    already_contacts = query_extension_user_link(user_id=user_id, linkedin_id=lid, contact_type=contact_tag)
    logger.info(f'user_id: {user_id} linkedin_profile: {linkedin_profile} contact_tag: {contact_tag} already_contacts: {already_contacts}')
    if already_contacts is None:
        already_contacts = []
    return len(already_contacts) > 0


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
    usage_func = get_contactout().query_usage
    assert contact_tag in ctx_map, f"user_fetch_contact only support {set(ctx_map.keys())}, but got: {contact_tag}"
    profile = process_profile(linkedin_profile)
    name, lid = info_from_profile(profile)
    global _PLM
    with _PLM.get_lock(profile=profile):
        logger.info(f"extension user {user_id} profile {profile} user_fetch_contact start run...")
        ctx = ctx_map[contact_tag]
        price = ctx['price']
        credit = fetch_user_credit(user_id=user_id)
        if credit is None:
            return None, f"user no credit"

        logger.info(f'extension user {user_id} need contact({contact_tag}) for {linkedin_profile}, his credit: {credit}, this time price: {price}')

        need_update_credit = True

        res = query_contact_by_profile(profile)
        db_item_exists = len(res) > 0
        db_content = json.loads(res[0][ctx['db_idx']]) if db_item_exists else None

        already_contacts = query_extension_user_link(user_id=user_id, linkedin_id=lid, contact_type=ctx['contact_type'])
        if already_contacts is None:
            already_contacts = []
        if len(already_contacts) == 0:
            if credit < price:
                logger.info(
                    f'extension user {user_id} credit {credit} insufficient for fetch {contact_tag}, which need {price}')
                return None, f"credit insufficient"
        need_update_already_contacts = True

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
            try:
                period, usage = usage_func()
                logger.info(f'echo outside usage: ({period}): {usage}')
            except BaseException as e:
                logger.info(f'fetch outside usage err: {e}')

            ## update db
            if db_item_exists:
                logger.info(
                    f'extension user {user_id} need contact({contact_tag}) for {profile}, id ({lid}), got outside {res}, now will update contact')
                ctx['update_db_func'](lid, res)
            else:
                logger.info(
                    f'extension user {user_id} need contact({contact_tag}) for {profile}, id ({lid}), got outside {res}, now will new contact')
                new_contact(linked_profile=profile, linkedin_id=lid, name=name, **{ctx['contact_type']: res})
        else:
            logger.info(f'extension user {user_id} need contact({contact_tag}) for {profile}, will from db, credit({credit}), will cost {price if len(already_contacts)== 0 else 0}')
            if len(already_contacts) > 0:
                need_update_already_contacts = False
                need_update_credit = False
                logger.info(
                    f'extension user {user_id} need contact({contact_tag}) for {profile}, already purchased, no need credit')
            res = db_content

        if need_update_credit:
            new_credit = credit - price
            update_user_credit(user_id=user_id, new_credit=new_credit)
            logger.info( f'extension user {user_id} need contact({contact_tag}) for {profile}, id ({lid}), new_credit: {new_credit}')

        if need_update_already_contacts:
            insert_extension_user_link(user_id=user_id, linkedin_id=lid, contact_type=ctx['contact_type'])
            logger.info(f"extension user {user_id} need contact({contact_tag}) for {profile}, id ({lid}), user link insert: {ctx['contact_type']}")

        return res, None


def refresh_contact(manage_account_id, candidate_id, profile):
    contact_info = profile['profile']['contactInfo']
    personal_email = contact_info['Email']
    phone = contact_info['Phone']

    logger.info(
        f"refresh_contact manage_account_id: {manage_account_id} candidate_id: {candidate_id} personal_email: {personal_email} phone: {phone}")
    refresh_contact_db(candidate_id, personal_email, phone)
    refresh_person_contact_db(manage_account_id, candidate_id, personal_email, phone)


def refresh_contact_db(candidate_id, personal_email, phone):
    if (personal_email is None or len(personal_email) == 0) and (phone is None or len(phone) == 0):
        return

    logger.info(f"refresh_contact_db candidate_id: {candidate_id} personal_email: {personal_email} phone: {phone}")
    has_record, person_emails, phones = query_contact_by_profile_id(candidate_id)

    if not has_record:
        linked_profile = "https://www.{}".format(candidate_id)
        name = candidate_id.split('/')[-1]
        personal_emails = []
        if personal_email is not None and len(personal_email) > 0:
            personal_emails.append(personal_email)
        phones = []
        if phone is not None and len(phone) > 0:
            phones.append(phone)
        new_contact(linked_profile, candidate_id, name, personal_email=personal_emails, work_email=[],
                    work_email_status=[], phone=phones)
        return

    if personal_email is not None and len(personal_email) > 0 and personal_email not in person_emails:
        update_contact_personal_email(candidate_id, [personal_email])
    if phone is not None and len(phone) > 0 and phone not in phones:
        update_contact_phone(candidate_id, [phone])


def refresh_person_contact_db(manage_account_id, candidate_id, personal_email, phone):
    logger.info(
        f"refresh_person_contact_db manage_account_id: {manage_account_id} candidate_id: {candidate_id} personal_email: {personal_email} phone: {phone}")
    if personal_email is not None and len(personal_email) > 0:
        origin_personal_email = query_extension_user_link(user_id=manage_account_id, linkedin_id=candidate_id,
                                                        contact_type="personal_email")
        if len(origin_personal_email) == 0:
            insert_extension_user_link(user_id=manage_account_id, linkedin_id=candidate_id,
                                       contact_type="personal_email")

    if phone is not None and len(phone) > 0:
        origin_phone = query_extension_user_link(user_id=manage_account_id, linkedin_id=candidate_id,
                                               contact_type="phone")
        if len(origin_phone) == 0:
            insert_extension_user_link(user_id=manage_account_id, linkedin_id=candidate_id, contact_type="phone")
