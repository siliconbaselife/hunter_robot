# -*- encoding:utf-8 -*-

import requests
import json
from requests_toolbelt import MultipartEncoder
from utils.config import config
from utils.log import get_logger
from dao.task_dao import *

logger = get_logger(config['log']['log_file'])
class GroupMsg:
    def __init__(self, con):
        self.corpid = con['corpid']
        self.app_list = con['app_list']
        self.agentid = con['agentid']
        self.corpsecret = con['corpsecret']
        self.request_url = con['request_url']

    def send_text(self, _message, useridlist=['name1|name2']):
        useridstr = "|".join(useridlist)  # userid 在企业微信-通讯录-成员-账号
        response = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}".format(
                corpid=self.corpid, corpsecret=self.corpsecret))
        data = json.loads(response.text)
        access_token = data['access_token']
        json_dict = {
            "touser": useridstr,
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": _message
            },
            "safe": 0,
            "enable_id_trans": 1,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        json_str = json.dumps(json_dict)
        response_send = requests.post(self.request_url, data=json_str)
        print("send to " + useridstr + ' ' + json.loads(response_send.text)['errmsg'])
        return json.loads(response_send.text)['errmsg'] == 'ok'

    def send_msg_info(self, msgs):
        r_msgs = "姓名："+ msgs['name'] + '\n'
        r_msgs += "简历：" + msgs["resume"] + "\n"
        r_msgs += "微信：" + msgs["wx"] + "\n"
        r_msgs += "电话：" + msgs["phone"] + "\n"
        r_msgs += "聊天：\n"
        for item in msgs["chat"]:
            r_msgs+= "\t"+json.dumps(item, ensure_ascii=False)+"\n"

        self.send_text(r_msgs, ['@all'])


def send_candidate_info(job_id, name, cv, wechat, phone, history_msg):
    ##这里用job_id取
    job_res = get_job_by_id(job_id)
    if len(job_res) == 0:
        logger.info(f"job config wrong, not exist: {job_id}, {name}")
    group_msg_config = json.loads(job_res[0][6])["group_msg"]

    con = config['group_msg'][group_msg_config]
    logger.info(f"group_msg_config: {job_id}, {name}, {con}")
    group_msg = GroupMsg(con)
    msgs = {
        "name": name,
        "resume": '' if cv is None else cv,
        "chat": history_msg,
        "wx": '' if wechat is None else wechat,
        "phone": '' if phone is None else phone
    }
    group_msg.send_msg_info(msgs)


if __name__ == "__main__":
    group_msg = GroupMsg()
    msgs = {
        "resume": "https://",
        "chat": [{"user": "你好", "robot": "你也好"}],
        "wx": "123456",
        "phone": "123456"
    }

    group_msg.send_msg_info(msgs)
