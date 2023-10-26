import random
import numpy as np
import copy
import json
from dao.task_dao import query_account_type_db,get_account_jobs_db
from service.task_service import get_job_by_id_service

def str_is_none(str):
    return str == None or str == "" or str == "None" or str == "NULL" or  str == "NONE" or str == "Null"


def format_time(time_obj, f_str='%Y-%m-%d %H:%M:%S'):
    return time_obj.strftime(f_str)


def deal_json_invaild(data):
    data = data.replace(' ','')
    data = data.replace("\n", "\\n").replace("\r", "\\r").replace("\n\r", "\\n\\r") \
        .replace("\r\n", "\\r\\n") \
        .replace("\t", "\\t")
    data = data.replace('":"', '&&testPassword1&&')\
        .replace('":', '&&testPassword2&&')\
        .replace('","', "$$testPassword$$")\
        .replace('{"', "@@testPassword@@")\
        .replace('"}', "**testPassword**")
    # print(data)

    data = data.replace('&&testPassword1&&', '":"').replace('&&testPassword2&&','":').replace('$$testPassword$$', '","').replace('@@testPassword@@', '{"').replace('**testPassword**', '"}')
    # print(data)
    data = data.replace("\'", "\\'")
    data = data.replace('\"', '\\"')
    return data


school_211 = '["北京大学","清华大学","复旦大学","上海交通大学","浙江大学","国防科技大学","中国人民大学","南京大学","中国科学技术大学","北京航空航天大学","同济大学","北京理工大学","东南大学","武汉大学","华中科技大学","哈尔滨工业大学","西安交通大学","南开大学","北京师范大学","华东师范大学","电子科技大学","中山大学","天津大学","厦门大学","华南理工大学","四川大学","西北工业大学","山东大学","重庆大学","中南大学","吉林大学","湖南大学","兰州大学","大连理工大学","中国农业大学","东北大学","中国海洋大学","中央民族大学","西北农林科技大学","郑州大学","云南大学","新疆大学","上海财经大学","北京邮电大学","中央财经大学","对外经济贸易大学","上海外国语大学","西安电子科技大学","中国政法大学","北京外国语大学","空军军医大学","北京交通大学","南京航空航天大学","南京理工大学","上海大学","西南财经大学","北京科技大学","华东理工大学","中国传媒大学","海军军医大学","北京工业大学","中南财经政法大学","河海大学","天津医科大学","苏州大学","东华大学","西南交通大学","华中师范大学","暨南大学","华北电力大学","南京师范大学","哈尔滨工程大学","武汉理工大学","陕西师范大学","华南师范大学","合肥工业大学","北京化工大学","中央音乐学院","西南大学","江南大学","东北师范大学","安徽大学","西北大学","福州大学","河北工业大学","北京林业大学","湖南师范大学","中国药科大学","北京中医药大学","中国地质大学（武汉）","南京农业大学","中国矿业大学（北京）","长安大学","中国矿业大学","中国石油大学（北京）","中国石油大学（华东）","海南大学","大连海事大学","南昌大学","华中农业大学","中国地质大学（北京）","辽宁大学","太原理工大学","贵州大学","北京体育大学","延边大学","广西大学","东北林业大学","四川农业大学","内蒙古大学","东北农业大学","宁夏大学","青海大学","石河子大学","西藏大学"]'
school_985 = '["北京大学","清华大学","上海交通大学","复旦大学","浙江大学","国防科技大学","中国科学技术大学","中国人民大学","南京大学","北京航空航天大学","北京理工大学","哈尔滨工业大学","西安交通大学","南开大学","同济大学","武汉大学","华中科技大学","北京师范大学","东南大学","四川大学","华东师范大学","电子科技大学","中山大学","天津大学","厦门大学","华南理工大学","西北工业大学","山东大学","重庆大学","中南大学","吉林大学","兰州大学","大连理工大学","中国农业大学","中国海洋大学","中央民族大学","湖南大学","东北大学","西北农林科技大学"]'
def is_211(school):
    return school in school_211

def is_985(school):
    return school in school_985

degree_dict = {
    "博士后": 4,
    "博士": 3,
    "硕士": 2,
    "本科": 1,
    "大专": 0,
    "高中": -1,
    "中专": -2,
    "初中及以下": -3,
    "中技": -4
}
def get_degree_num(degree_str):
    return degree_dict[degree_str]



def encrypt(text, key):
    encrypted_text = ""
    for char in text:
        if char.isalpha():
            shift = 65 if char.isupper() else 97
            encrypted_char = chr((ord(char) - shift + key) % 26 + shift)
        else:
            encrypted_char = char
        encrypted_text += encrypted_char
    return encrypted_text

def decrypt(encrypted_text, key):
    decrypted_text = ""
    for char in encrypted_text:
        if char.isalpha():
            shift = 65 if char.isupper() else 97
            decrypted_char = chr((ord(char) - shift - key) % 26 + shift)
        else:
            decrypted_char = char
        decrypted_text += decrypted_char
    return decrypted_text


key = 3
original_text = "Hello, World!"
encrypted_text = encrypt(original_text, key)
decrypted_text = decrypt(encrypted_text, key)

print("原始文本:", original_text)
print("加密后:", encrypted_text)
print("解密后:", decrypted_text)


def generate_random_digits(length):
    return ''.join(random.choice('0123456789') for _ in range(length))

api_config = [
    {
        "label":"作业帮",
        "value":"/vision/chat/receive/message/v1",
        "robot_template":""
    },{
        "label":"民生银行",
        "value":"/vision/chat/receive/message/minsheng/v1",
        "robot_template":""
    },{
        "label":"滴滴客服",
        "value":"/vision/chat/receive/message/unicom/v1",
        "robot_template":""
    },{
        "label":"北京通用客服",
        "value":"/vision/chat/receive/message/generic/v1",
        "robot_template":""
    },{
        "label":"石家庄情感顾问",
        "value":"/vision/chat/receive/message/emotional/v1",
        "robot_template":""
    },{
        "label":"NLP算法工程师-头条",
        "value":"/vision/chat/receive/message/emotional/v1",
        "robot_template":""
    },{
        "label":"remoly海外bd",
        "value":"/vision/chat/receive/message/remoly/v1",
        "robot_template":""
    },{
        "label":"地平线自动驾驶感知算法工程师",
        "value":"/vision/chat/receive/message/drive/v1",
        "robot_template":""
    },{
        "label":"海外销售岗",
        "value":"/vision/chat/receive/message/overseas/v1",
        "robot_template":""
    },{
        "label":"快手商家一线",
        "value":"/vision/chat/receive/message/kwai_service/v1",
        "robot_template":""
    },{
        "label":"快手消费者二线",
        "value":"/vision/chat/receive/message/kwai_outbound/v1",
        "robot_template":""
    },{
        "label":"aigc工程师",
        "value":"/vision/chat/receive/message/aigc/v1",
        "robot_template":""
    },{
        "label":"图像算法工程师",
        "value":"/vision/chat/receive/message/cv/v1",
        "robot_template":""
    }
]

manage_account_dict = {
    "jiajia.zhao": list(np.array(api_config).take([5,7,8,11,12])),
    "jiajia.zhao2": list(np.array(api_config).take([5,7,8,11,12])),
    "manage_test": api_config,
    "manage_test2": api_config,
    "jane": list(np.array(api_config).take([5,7,8,11,12])),
    "yao": list(np.array(api_config).take([0,2,4])),
    "zjj.test1":list(np.array(api_config).take([5])),
    "zjj.test2":list(np.array(api_config).take([5])),
    "zjj.test3":list(np.array(api_config).take([5])),
    "zjj.test4":list(np.array(api_config).take([5])),
    "zjj.test5":list(np.array(api_config).take([5])),
    "zjj.test6":list(np.array(api_config).take([5])),
    "zjj.test7":list(np.array(api_config).take([5])),
    "zjj.test8":list(np.array(api_config).take([5])),
    "zjj.test9":list(np.array(api_config).take([5])),
    "zjj.test10":list(np.array(api_config).take([5])),
    "zjj.test11":list(np.array(api_config).take([5])),
    "zjj.test12":list(np.array(api_config).take([5])),
    "zjj.test13":list(np.array(api_config).take([5])),
    "zjj.test14":list(np.array(api_config).take([5])),
    "zjj.test15":list(np.array(api_config).take([5])),
    "zjj.test16":list(np.array(api_config).take([5])),
    "zjj.test17":list(np.array(api_config).take([5])),
    "zjj.test18":list(np.array(api_config).take([5])),
    "zjj.test19":list(np.array(api_config).take([5])),
    "zjj.test20":list(np.array(api_config).take([5]))
}

statistic_id_dict = {
    "zjj0101": ["jane", "jiajia.zhao", "jiajia.zhao2", "zjj.test1", "zjj.test2", "zjj.test3", "zjj.test4", "zjj.test5", "zjj.test6", "zjj.test7", "zjj.test8", "zjj.test9", "zjj.test10",
                "zjj.test11", "zjj.test12", "zjj.test13", "zjj.test14", "zjj.test15", "zjj.test16", "zjj.test17", "zjj.test18", "zjj.test19", "zjj.test20"]
}

default_job_map = {
    "maimai": {
        "zp":"job_maimai_default-manual-id",
        "bd":"job_maimai_overseas-bd-manual-id",
        "wm":"job_maimai_overseas-bd-manual-id"
    },
    "Boss": {
        "zp":"job_boss_default-manual-id",
        "bd":"job_boss_default-manual-id",
        "wm":"job_boss_default-manual-id"
    },
    "Linkedin":{
        "zp":"job_linkedin_default-manual-id",
        "bd":"job_maimai_overseas-bd-manual-id",
        "wm":"job_maimai_overseas-bd-manual-id"
    }
}

def get_default_job(account_id, jobs, platform_type):
    if len(jobs) == 0:
        return default_job_map[platform_type]["zp"]
    else:
        job_ret = get_job_by_id_service(jobs[0])[0]
        job_config = json.loads(job_ret[6])
        if 'recall_config' in job_config:
            recall_type = job_config['recall_config']
        else:
            recall_type = 'zp'
        return default_job_map[platform_type][recall_type]

def get_stat_id_dict():
    return statistic_id_dict

def get_api_conifg(manage_account_id):
    if manage_account_id in manage_account_dict:
        return copy.deepcopy(manage_account_dict[manage_account_id])
    else:
        return []

def process_str(s):
    s = s.replace('\\n',',')
    s = s.replace('\n',',') 
    s = s.replace('，',',')
    return s

def process_list(str_list):
    ret = []
    for s in str_list:
        s = s.replace('，',',')
        s = s.replace('\\n',',')
        s = s.replace('\n',',')
        ret.extend(s.split(','))
    return ret

def process_str_to_list(s):
    s = s.replace(':',',')
    s = s.replace('.',',')
    s = s.replace('。',',')
    s = s.replace('、',',')
    s = s.replace('，',',')
    s = s.replace('\\n',',')
    s = s.replace('\n',',')
    return s.split(',')
