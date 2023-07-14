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
config['chat']['chat_url'] = 'http://127.0.0.1:12222/vision/chat/receive/message/v1'
