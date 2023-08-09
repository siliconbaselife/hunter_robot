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
    'need_contact_on_refuse': [
        '方便给我留一个联系方式么，我这里也有其他岗位可以推荐给您',
        '您方便留下您的联系方式么？我这里还有其他岗位机会，可能会适合您。',
        "或许我们还有其他岗位符合您的兴趣和技能。是否可以留个联系方式，方便我向您推荐？",
        '如果您方便，能否把您的联系方式留下？我会帮您寻找适合您的其他职位。',
        '您能留下联系方式么？我会帮您探索其他职位的机会，看看是否有合适的岗位适合您。'
    ],
    'need_contact_normal': [
        '咱能不能留个简历和联系方式呢',
        '您方便留个联系方式么，我们可以详细沟通一下',
        "您能否告诉我一个可以与您详细沟通的联系方式呢？",
        "希望跟您进一步沟通一下，能否留下您的联系方式？",
        "可否告知一下您的联系方式，以便我们进行后续沟通？",
        "我们想要邀请您参与进一步的面试流程，您方便留下联系方式？"
        "为了更好地安排后续的步骤，您能否提供一个可以联系到您的方式？"
        "您是否可以留下一个可以联系到您的号码？"
        "您是否能够提供一个有效的联系方式，以便我们能够进一步交流？"
        "您能将您的联系方式留一下么，我们好安排后续的面试流程。"
    ],
    'trivial_case': [''],
    'got_contact': [
        '我们这边hr稍后会跟您详细沟通', 
        '好的，hr会跟您进一步沟通',
        '谢谢。HR会尽快与您沟通，安排下一步的流程',
        '我们hr会尽快跟您联系',
        'HR会尽快与您联络，来安排后续流程'
    ]
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