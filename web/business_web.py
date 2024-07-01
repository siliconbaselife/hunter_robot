from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math

from service.business_service import get_consultant, session_query_service

business_web = Blueprint('business_web', __name__, template_folder='templates')

logger = get_logger(config['log']['business_log_file'])

@business_web.route("/backend/business/analysis", methods=['POST'])
@web_exception_handler
def business_analysis_api():
    user_id = request.json.get('user_id', None)
    chat_id = request.json.get('chat_id', None)
    job = request.json.get('job', None)
    src_company = request.json.get('src_company', None)
    region = request.json.get('region', None)
    platform = request.json.get('platform', '领英')
    jd = request.json.get('jd', None)
    if user_id is None:
        return Response(json.dumps(get_web_res_fail("user_id 需要指定"), ensure_ascii=False))
    if jd is None:
        return Response(json.dumps(get_web_res_fail("jd 内容需要指定"), ensure_ascii=False))
    
    if chat_id is not None and len(chat_id)==0:
        chat_id = None

    ret = get_consultant(user_id=user_id, consultant_id=chat_id)(src_company=src_company, target_region=region, job=job, question=jd, platform=platform)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@business_web.route("/backend/business/session", methods=['POST'])
def agent_sess_api():
    user_id = request.json.get('user_id', None)
    if user_id is None:
        return Response(json.dumps(get_web_res_fail("user_id 需要指定"), ensure_ascii=False))
    ret = session_query_service(user_id)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))


@business_web.route("/backend/business/history", methods=['POST'])
@web_exception_handler
def agent_history_api():
    user_id = request.json.get('user_id', None)
    if user_id is None:
        return Response(json.dumps(get_web_res_fail("user_id 需要指定"), ensure_ascii=False))
    chat_id = request.json.get('chat_id', None)
    if chat_id == None:
        return Response(json.dumps(get_web_res_fail("chat_id 内容需要指定"), ensure_ascii=False))
    ret = get_consultant(user_id=user_id, consultant_id=chat_id).history()
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
