config = {
    'log': {},
    'task':{},
    'chat':{},
    'db': {}
}

config['db']['host'] = 'localhost'
config['db']['port'] = 3306
config['db']['name'] = 'recruit_data_v2'
config['db']['user'] = 'chat_user'
config['db']['pwd'] = '1'

config['log']['log_file'] = 'log/recurit_service.log'

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
    ]
}

config['chat'] = dict()
config['chat']['preset_reply'] = {
    'need_contact': '咱能不能留个简历和联系方式呢',
    'finish_fail': '好的，那知道了，如果后面有需要，再联系我。',
    'got_contact': 'hr稍后会跟您联系'
}
config['chat']['trivial_reply_intent'] = [
    '询问此岗位不相关的概念',
    '询问人事其它业务',
    '拒绝',
    '感谢',
    '过激语言',
    '考虑',
    '确认',
    '无法独立判断意图的语料'
]

config['chat']['chat_url'] = 'http://127.0.0.1:12222'