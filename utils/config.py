config = {
    'log': {},
    'task':{},
    'chat':{},
    'db': {},
    'group_msg':{}
}

config['db']['host'] = 'localhost'
config['db']['port'] = 3306
config['db']['name'] = 'recruit_data_v2_beta'
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
    ],
    "filter": {
        "city": {"area": "北京"},
        "education": ["中专/中技","高中","大专","本科","硕士","博士"],
        "pay": ["5-10K"],
        "status": ["离职-随时到岗"]
    }
}

config['chat'] = dict()
config['chat']['preset_reply'] = {
    'need_contact_on_refuse': ['咱能不能留个简历和联系方式呢'],
    'need_contact_normal': ['咱能不能留个简历和联系方式呢'],
    'trivial_case': [''],
    'got_contact': ['hr稍后会跟您联系']
}

config['chat']['trivial_intent'] = [
    '询问此岗位不相关的概念',
    '询问人事其它业务',
    '感谢',
    '过激语言',
    '考虑',
    '确认',
    '无法独立判断意图的语料'
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