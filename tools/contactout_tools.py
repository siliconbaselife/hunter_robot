import json
import time
import requests

from utils.log import get_logger
from utils.config import config as config

logger = get_logger(config['log']['extension_log_file'])

class ContactOut(object):
    url_base = 'https://api.contactout.com/v1/people/linkedin'
    person_email_uri = 'personal_email_status'
    work_email_uri = 'work_email_status'
    phone_num_uri = 'phone_status'
    token = config['extension']['contactout']['token']

    def email_status(self, profile, is_work_email):
        email_uri = self.work_email_uri if is_work_email else self.person_email_uri
        req_url = f'{self.url_base}/{email_uri}?profile={profile}'
        headers = {
            'authorization': 'basic',
            'token': self.token,
        }
        res = requests.get(req_url, headers=headers)
        logger.info(f'request contactout record: {email_uri}: {res.text}')
        assert res.status_code==200, f"email_status({email_uri}) for {profile} request to contact out abnormal: {res.text}"
        res = res.json()
        assert res['status_code']==200, f"email_status({email_uri}) for {profile} data from contact out abnormal: {res}"
        res = res['profile']
        has_email = res.get('email', False)
        email_status = res.get('email_status', None)
        return has_email, email_status

    def phone_status(self, profile):
        req_url = f'{self.url_base}/{self.phone_num_uri}?profile={profile}'
        headers = {
            'authorization': 'basic',
            'token': self.token,
        }
        res = requests.get(req_url, headers=headers)
        logger.info(f'request contactout record: {self.phone_num_uri}: {res.text}')
        assert res.status_code==200, f"phone_status for {profile} request to contact out abnormal: {res.text}"
        res = res.json()
        assert res['status_code']==200, f"phone_status for {profile} data from contact out abnormal: {res}"
        res = res['profile']
        has_phone = res.get('phone', False)
        return has_phone, None

    def fetch_email(self, profile):
    # def fetch_email(self, profile, is_work_email):
        # email_type='work' if is_work_email else 'personal'
        # req_url = f'{url_base}?profile={profile}&email_type={email_type}'
        req_url = f'{self.url_base}?profile={profile}'
        headers = {
            'authorization': 'basic',
            'token': self.token,
        }
        res = requests.get(req_url, headers=headers)
        logger.info(f'request contactout record: {req_url}: {res.text}')
        assert res.status_code==200, f"fetch_email for {profile} request to contact out abnormal: {res.text}"
        res = res.json()
        assert res['status_code']==200, f"fetch_email for {profile} data from contact out abnormal: {res}"
        res = res['profile']
        return {
            'personal_email': res['personal_email'],
            'work_email': res['work_email'],
            'work_email_status': res['work_email_status'],
        }

    def fetch_phone(self, profile):
        req_url = f'{self.url_base}?profile={profile}&include_phone=true'
        headers = {
            'authorization': 'basic',
            'token': self.token,
        }
        res = requests.get(req_url, headers=headers)
        logger.info(f'request contactout record: {req_url}: {res.text}')
        assert res.status_code==200, f"fetch_phone for {profile} request to contact out abnormal: {res.text}"
        res = res.json()
        assert res['status_code']==200, f"fetch_phone for {profile} data from contact out abnormal: {res}"
        res = res['profile']
        return {
            'personal_email': res['personal_email'],
            'work_email': res['work_email'],
            'work_email_status': res['work_email_status'],
            'phone': res['phone']
        }

_contact_out = None
def get_contactout():
    global _contact_out
    if not _contact_out:
        _contact_out = ContactOut()

    return _contact_out