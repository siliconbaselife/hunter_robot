config = {
    'log': {},
    'task':{},
    'chat':{},
    'db': {},
    'group_msg':{},
    'llm': {},
    'business': {},
    'extension': {}
}

config['db']['host'] = 'localhost'
config['db']['port'] = 3306
config['db']['name'] = 'recruit_data_v2'
config['db']['user'] = 'chat_user'
config['db']['pwd'] = '1'

config['log']['log_file'] = 'log/recurit_service.log'
config['log']['business_log_file'] = 'log/business_log.log'
config['log']['extension_log_file'] = 'log/extension_log.log'

config['task']['task_config_base'] = {
    "helloSum": 50,
    "taskType": "batchTouch",
    "timeMount": [
      {
        "time": "09:00",
        "mount": 25
      },
      {
        "time": "16:00",
        "mount": 25
      }
    ],
    "filter": {
        "city": {"area": "北京"},
        "education": ["中专/中技","高中","大专","本科","硕士","博士"],
        "pay": ["5-10K"],
        "status": ["离职-随时到岗"]
    }
}

config['chat'] = dict()

config['chat']['trivial_intent'] = [
    '询问此岗位不相关的概念',
    '询问人事其它业务',
    '感谢',
    '过激语言',
    '考虑',
    '确认',
    '无法独立判断意图的语料',
    'nlu_fallback'
]

config['chat']['refuse_intent'] = ['拒绝']

config['chat']['chat_url'] = 'http://127.0.0.1:12222'





#=========================
# msg config
config['group_msg'] = dict()
config['group_msg']['shijiazhuang'] = {
    'corpid':'ww0ee23e06934cd92c',
    'app_list': [
            (1000005, 'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM')
        ],
    'agentid': 1000005,
    'corpsecret':'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM',
    'request_url':"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=491e411f-c325-4096-aabc-294dadf8f8b8"
}
config['group_msg']['beijing'] = {
    'corpid':'ww0ee23e06934cd92c',
    'app_list': [
            (1000005, 'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM')
        ],
    'agentid': 1000005,
    'corpsecret':'yWATRUgt1kazQexpdzbqkisTGkMgGqpw7eSpd0qKPlM',
    'request_url':'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c407cd12-b7c7-4038-8cc4-4e9cb71dbbc1'
}


#==========================



# job register config
config['job_register'] = {
    "Boss":{
        "filter_config":"boss_autoload_filter",
        "filter_config_v2":"boss_autoload_filter_v2",
        "chat_config":"base_common_chat",
        "chat_config_v2":"main_chat_robot_v2",
        "chat_config_v3":"main_chat_robot_v3",
        "recall_config":"zp"
    },
    "Linkedin":{
        "filter_config":"linkedin_autoload_filter",
        "filter_config_v2":"linkedin_autoload_filter_v2",
        "custom_filter_config":"linkedin_custom_filter",
        "chat_config":"base_common_chat",
        "chat_config_v2":"main_chat_robot_v2",
        "recall_config":"zp"
    },
    "maimai":{
        "filter_config":"maimai_autoload_filter",
        "filter_config_v2":"maimai_autoload_filter_v2",
        "custom_filter_config":"maimai_custom_filter",
        "chat_config":"maimai_common_chat",
        "chat_config_v2":"main_chat_robot_v2",
        "recall_config":"zp"
    },
    "liepin":{
        "filter_config_v2":"liepin_autoload_filter_v2",
        "custom_filter_config":"liepin_custom_filter",
        "chat_config_v2":"main_chat_robot_v2",
        "recall_config":"zp"
    }
}


config['llm']['gemini'] = {
    'api_key': 'AIzaSyASOB4k_gyjPsUQZkgrm3_hw2PkyBgMI9o',
    'model_type': 'gemini-pro',
}

config['business']['expired_time_s'] = 3600

config['extension']['contactout'] = {
    'token': 'W3CA5nrUdUEn3N0ThFwqcjsC',
}

config['extension']['price'] = {
    'personal_email': 20,
    'work_email': 10,
    'phone': 40,
}