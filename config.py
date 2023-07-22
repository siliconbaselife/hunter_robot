config = dict()

config['log_file'] = 'recurit_service.log'

# db
config['db'] = dict()
config['db']['host'] = 'localhost'
config['db']['port'] = 3306
config['db']['name'] = 'recruit_data'
config['db']['user'] = 'chat_user'
config['db']['pwd'] = '1'

config['chat'] = dict()
config['chat']['mock'] = False
config['chat']['mock_preset'] = ["十分感谢我们这边的职位", "您的问题我们已经记录了，确认好了之后给您回复", "祝您生活愉快"]
config['chat']['preset_reply'] = {
    'need_contact': '\n咱能不能留个简历和联系方式呢',
    'finish_fail': '\n好的，那知道了，如果后面有需要，再联系我。'
}

config['chat']['chat_url'] = 'http://127.0.0.1:12222'
