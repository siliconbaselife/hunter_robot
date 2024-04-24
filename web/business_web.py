from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math

from service.business_service import get_consultant

business_web = Blueprint('business_web', __name__, template_folder='templates')

logger = get_logger(config['log']['business_log_file'])

@business_web.route("/backend/business/target_company", methods=['POST'])
@web_exception_handler
def search_target_company_api():
    job = request.json.get('job', None)
    if job == None:
        return Response(json.dumps(get_web_res_fail("job 未指定"), ensure_ascii=False))
    src_company = request.json.get('src_company', None)
    if src_company == None:
        return Response(json.dumps(get_web_res_fail("src_company 未指定"), ensure_ascii=False))
    region = request.json.get('region', None)
    if region == None:
        return Response(json.dumps(get_web_res_fail("region 未指定"), ensure_ascii=False))
    jd = request.json.get('jd', None)
    if jd == None:
        return Response(json.dumps(get_web_res_fail("jd 未指定"), ensure_ascii=False))

    chat_id, res_msg = find_target_company(src_company=src_company, target_region=region, job=job, jd=jd)
    ret = {
        'chat_id': chat_id,
        'res': res_msg
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@business_web.route("/backend/business/keyword", methods=['POST'])
@web_exception_handler
def find_keyword_api():
    job = request.json.get('job', None)
    if job == None:
        return Response(json.dumps(get_web_res_fail("job 未指定"), ensure_ascii=False))
    jd = request.json.get('jd', None)
    if jd == None:
        return Response(json.dumps(get_web_res_fail("jd 未指定"), ensure_ascii=False))
    platform = request.json.get('platform', '领英')
    if platform == None:
        return Response(json.dumps(get_web_res_fail("platform 未指定"), ensure_ascii=False))

    chat_id, res_msg = find_platform_keyword(job=job, jd=jd, platform=platform)
    ret = {
        'chat_id': chat_id,
        'res': res_msg
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))

@business_web.route("/backend/business/analysis", methods=['POST'])
@web_exception_handler
def business_analysis_api():
    chat_id = request.json.get('chat_id', None)
    job = request.json.get('job', None)
    src_company = request.json.get('src_company', None)
    region = request.json.get('region', None)
    platform = request.json.get('platform', '领英')
    jd = request.json.get('jd', None)
    if jd == None:
        return Response(json.dumps(get_web_res_fail("jd 内容需要指定"), ensure_ascii=False))

    ret = get_consultant(consultant_id=chat_id)(src_company=src_company, target_region=region, job=job, question=jd, platform=platform)
    return Response(json.dumps(get_web_res_suc_with_data(ret), ensure_ascii=False))
