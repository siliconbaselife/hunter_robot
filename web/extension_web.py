from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math

from service.extension_service import new_extension_user, fetch_user_credit, update_user_credit, user_fetch_contact, query_user_contact

extension_web = Blueprint('extension_web', __name__, template_folder='templates')

logger = get_logger(config['log']['extension_log_file'])

@extension_web.route("/backend/extension/user/credit/refill", methods=['POST'])
@web_exception_handler
def refill_credit_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    refill_credit = request.json.get('refill_credit', None)
    if refill_credit == None or type(refill_credit) is not int:
        return Response(json.dumps(get_web_res_fail(f"refill_credit invalid: {refill_credit}"), ensure_ascii=False))

    credit = fetch_user_credit(user_id=user_id)
    credit+= refill_credit
    update_user_credit(user_id=user_id, new_credit=credit)
    ret = {
        'updated_credit': credit
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@extension_web.route("/backend/extension/user/credit/query", methods=['POST'])
@web_exception_handler
def fetch_user_credit_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    credit = fetch_user_credit(user_id=user_id)
    if not credit:
        return Response(json.dumps(get_web_res_fail(f"user {user_id} not in system"), ensure_ascii=False))

    ret = {
        'credit': credit
    }

    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@extension_web.route("/backend/extension/user/contact/judge", methods=['POST'])
@web_exception_handler
def judge_user_contact_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    linkedin_profile = request.json.get('linkedin_profile', None)
    if linkedin_profile == None:
        return Response(json.dumps(get_web_res_fail("linkedin_profile 未指定"), ensure_ascii=False))
    contact_type = request.json.get('contact_type', None)
    if contact_type == None:
        return Response(json.dumps(get_web_res_fail("contact_type 未指定"), ensure_ascii=False))
    is_contact = query_user_contact(user_id=user_id, linkedin_profile=linkedin_profile, contact_type=contact_type)
    ret = {
        'is_contact': is_contact
    }

    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@extension_web.route("/backend/extension/contact/personalemail", methods=['POST'])
@web_exception_handler
def fetch_personal_email_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    linkedin_profile = request.json.get('linkedin_profile', None)
    if linkedin_profile == None:
        return Response(json.dumps(get_web_res_fail("linkedin_profile 未指定"), ensure_ascii=False))
    res, msg = user_fetch_contact(user_id=user_id, linkedin_profile=linkedin_profile, contact_tag='personal_email')
    ret = {
        'msg': msg
    }
    if res is not None:
        ret['personal_email'] = res
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@extension_web.route("/backend/extension/contact/phone", methods=['POST'])
@web_exception_handler
def fetch_phone_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    linkedin_profile = request.json.get('linkedin_profile', None)
    if linkedin_profile == None:
        return Response(json.dumps(get_web_res_fail("linkedin_profile 未指定"), ensure_ascii=False))
    res, msg = user_fetch_contact(user_id=user_id, linkedin_profile=linkedin_profile, contact_tag='phone')
    ret = {
        'msg': msg
    }
    if res is not None:
        ret['phone'] = res
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
