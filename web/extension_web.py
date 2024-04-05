from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math

from service.extension_service import new_extension_user, fetch_user_credit, user_fetch_personal_email

extension_web = Blueprint('extension_web', __name__, template_folder='templates')

logger = get_logger(config['log']['extension_log_file'])

@extension_web.route("/backend/extension/user/register", methods=['POST'])
@web_exception_handler
def register_user_api():
    user_email = request.json.get('user_email', None)
    if user_email == None:
        return Response(json.dumps(get_web_res_fail("user_email 未指定"), ensure_ascii=False))
    credit = request.json.get('credit', 0)
    user_id = new_extension_user(user_email, credit)
    ret = {
        'user_id': user_id
    }

    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@extension_web.route("/backend/extension/user/credit", methods=['POST'])
@web_exception_handler
def fetch_user_credit_api():
    user_id = request.json.get('user_id', None)
    if user_id == None:
        return Response(json.dumps(get_web_res_fail("user_id 未指定"), ensure_ascii=False))
    credit = fetch_user_credit(user_id=user_id)
    ret = {
        'credit': credit
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
    res, msg = user_fetch_personal_email(user_id=user_id, linkedin_profile=linkedin_profile)
    ret = {
        'msg': msg
    }
    if res is not None:
        ret['personal_email'] = res
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
