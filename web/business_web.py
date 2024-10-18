from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

from utils.utils import key, decrypt

import json
import math

from service.business_service import *

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

    if chat_id is not None and len(chat_id) == 0:
        chat_id = None

    ret = get_consultant(user_id=user_id, consultant_id=chat_id)(src_company=src_company, target_region=region, job=job,
                                                                 question=jd, platform=platform)
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


@business_web.route("/backend/business/history/delete", methods=['POST'])
@web_exception_handler
def agent_history_del_api():
    user_id = request.json.get('user_id', None)
    if user_id is None:
        return Response(json.dumps(get_web_res_fail("user_id 需要指定"), ensure_ascii=False))
    chat_id = request.json.get('chat_id', None)
    if chat_id == None:
        return Response(json.dumps(get_web_res_fail("chat_id 内容需要指定"), ensure_ascii=False))
    del_history_service(chat_id)
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))


@business_web.route("/backend/agent/history/delete", methods=['POST'])
@web_exception_handler
def agent_history_del():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name is None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        user_id = decrypt(cookie_user_name, key)
    session_id = request.json.get('session_id', None)
    logger.info(f"delete agent history user_id: {user_id} session id: {session_id}")
    agent_history_remove_service(user_id, session_id)
    return Response(json.dumps(get_web_res_suc_with_data(None), ensure_ascii=False))


@business_web.route("/backend/agent/history/list", methods=['POST'])
@web_exception_handler
def agent_history_list():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name is None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        user_id = decrypt(cookie_user_name, key)
    history_list = agent_history_list_service(user_id)
    return Response(json.dumps(get_web_res_suc_with_data(history_list), ensure_ascii=False))


@business_web.route("/backend/agent/history/get", methods=['POST'])
@web_exception_handler
def agent_history_get():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name is None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        user_id = decrypt(cookie_user_name, key)
    session_id = request.json.get('session_id', None)
    history = agent_history_get_service(user_id, session_id)
    return Response(json.dumps(get_web_res_suc_with_data(history), ensure_ascii=False))


@business_web.route("/backend/agent/history/chat", methods=['POST'])
@web_exception_handler
def agent_history_chat():
    cookie_user_name = request.cookies.get('user_name', None)
    if cookie_user_name is None:
        return Response(json.dumps(get_web_res_fail("未登录"), ensure_ascii=False))
    else:
        user_id = decrypt(cookie_user_name, key)
    session_id = request.json.get('session_id', None)
    msg = request.json.get('msg', None)
    r_msg_info, session_id = agent_chat_service(user_id, session_id, msg)
    return Response(
        json.dumps(get_web_res_suc_with_data({"session_id": session_id, "r_msg": r_msg_info}), ensure_ascii=False))


@business_web.route("/backend/agent/functions", methods=['POST'])
@web_exception_handler
def agent_functions():
    functions = agent_functions_get_service()
    return Response(json.dumps(get_web_res_suc_with_data(functions), ensure_ascii=False))


@business_web.route("/backend/agent/chat_stream", methods=['POST'])
@web_exception_handler
def chat_stream():
    def event_stream():
        session_id = '123456'
        content = ''
        count = 0
        while count < 10:
            resData = {"session_id": session_id, "r_msg": str(count)}
            yield f"data: {json.dumps(get_web_res_suc_with_data(resData))}\n\n"
            content += str(count)
            count += 1
            time.sleep(1)
        finalResData = {"session_id": session_id, "r_msg": content}
        yield f"event: end\ndata: {json.dumps(get_web_res_suc_with_data(finalResData))}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')
