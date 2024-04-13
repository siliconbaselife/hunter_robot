from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
from service.chat_plugin_service import conf as service_conf, get_conf as service_get_conf, chat as service_chat

import json

logger = get_logger(config['log']['log_file'])

chat_web = Blueprint('chat_web', __name__, template_folder='templates')


@chat_web.route("/backend/chat/conf", methods=['POST'])
@web_exception_handler
def conf():
    user_id = request.json.get('user_id')
    tag = request.json.get('tag')
    conf = request.json.get('content')
    logger.info(f"获取到 {user_id} {tag} 的配置: {conf}")
    service_conf(user_id, tag, conf)

    return Response(json.dumps(get_web_res_suc_with_data({"success": True}), ensure_ascii=False))


@chat_web.route("/backend/chat/get_conf", methods=['POST'])
@web_exception_handler
def get_conf():
    user_id = request.json.get('user_id')
    logger.info(f"{user_id} 需要获取对话配置")
    confs = service_get_conf(user_id)

    return Response(json.dumps(get_web_res_suc_with_data(confs), ensure_ascii=False))


@chat_web.route("/backend/chat/chat", methods=['POST'])
@web_exception_handler
def chat():
    user_id = request.json.get('user_id')
    account_id = request.json.get('account_id')
    candidate_id = request.json.get('candidate_id')
    details = request.json.get('details')

    return_msgs = service_chat(user_id, account_id, candidate_id, details)

    return Response(json.dumps(get_web_res_suc_with_data(return_msgs), ensure_ascii=False))