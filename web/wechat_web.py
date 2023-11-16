from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from service.wechat_service import *
import json
import math
import traceback
from datetime import datetime


logger = get_logger(config['log']['log_file'])

wechat_web = Blueprint('wechat_web', __name__, template_folder='templates')


@wechat_web.route("/wechat/candidate/taskToDo", methods=['POST'])
@web_exception_handler
def task_fetch_api():
    wechat_account_id = request.json['accountID']
    logger.info(f'wechat_task_fetch_request, {wechat_account_id}')
    task_list = task_to_do(wechat_account_id)
    logger.info(f'wechat_task_fetch_list, {wechat_account_id}: {task_list}')
    ret_data = {
        'task': task_list
    }
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@wechat_web.route("/wechat/candidate/msgSendReport", methods=['POST'])
@web_exception_handler
def msg_send_report():
    wechat_account_id = request.json['account_id']
    wechat_alias_id = request.json['alias_id']
    msg_send = request.json['msg_send']
    logger.info(f'wechat_own_msg_send:{wechat_account_id}, {wechat_alias_id}, {msg_send}')
    own_msg_report(wechat_account_id, wechat_alias_id, msg_send)
    return Response(json.dumps(get_web_res_suc_with_data()))

@wechat_web.route("/wechat/candidate/addFriendReport", methods=['POST'])
@web_exception_handler
def add_friend_report():
    wechat_account_id = request.json['account_id']
    wechat_alias_id = request.json['alias_id']
    wechat_id = request.json['search_id']
    logger.info(f'wechat_add_friend_report:{wechat_account_id}, {wechat_alias_id}, {wechat_id}')
    friend_report(wechat_account_id, wechat_alias_id, wechat_id)
    return Response(json.dumps(get_web_res_suc_with_data()))

@wechat_web.route("/wechat/candidate/userMsg", methods=['POST'])
@web_exception_handler
def user_msg():
    wechat_account_id = request.json['account_id']
    wechat_alias_id = request.json['alias_id']
    msg_receive = request.json['msg_receive']
    logger.info(f'wechat_user_msg_received:{wechat_account_id}, {wechat_alias_id}, {msg_receive}')
    user_msg_report(wechat_account_id, wechat_alias_id, msg_receive)
    return Response(json.dumps(get_web_res_suc_with_data()))


