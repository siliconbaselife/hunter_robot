# -*- encoding:utf-8 -*-

import requests
import json
from requests_toolbelt import MultipartEncoder


class GroupMsg:
    def __init__(self):
        self.corpid = 'ww0ee23e06934cd92c'
        self.app_list = [
            (1000005, 'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM')
        ]
        self.agentid = 1000005
        self.corpsecret = 'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM'

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
        response_send = requests.post(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c407cd12-b7c7-4038-8cc4-4e9cb71dbbc1", data=json_str)
        print("send to " + useridstr + ' ' + json.loads(response_send.text)['errmsg'])
        return json.loads(response_send.text)['errmsg'] == 'ok'

    def send_msg_info(self, msgs):
        r_msgs = ""
        r_msgs += "聊天:" + json.dumps(msgs["chat"], ensure_ascii=False) + "\n"
        r_msgs += "简历:" + msgs["resume"] + "\n"
        r_msgs += "微信:" + msgs["wx"] + "\n"
        r_msgs += "电话" + msgs["phone"] + "\n"

        self.send_text(r_msgs, ['@all'])


if __name__ == "__main__":
    group_msg = GroupMsg()
    msgs = {
        "resume": "https://",
        "chat": [{"user": "你好", "robot": "你也好"}],
        "wx": "123456",
        "phone": "123456"
    }

    group_msg.send_msg_info(msgs)
