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
    account_id = request.json['accountID']
    logger.info(f'account task fetch request {account_id}')
    task_list = get_undo_task(account_id)

    logger.info(f'account task fetch {account_id}: {task_list}')
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
    return Response(json.dumps(get_web_res_suc_with_data(ret_data)))

@wechat_web.route("/wechat/candidate/addFriendReport", methods=['POST'])
@web_exception_handler
def add_friend_report():


    return

@wechat_web.route("/wechat/candidate/userMsg", methods=['POST'])
@web_exception_handler
def user_msg():
    return