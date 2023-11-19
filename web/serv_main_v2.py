from flask import Flask
from utils.log import get_logger
from flask_cors import *
from web.source_web import source_web
from web.wechat_web import wechat_web
from web.manage_web import manage_web
from utils.config import config
from dao.task_dao import *
logger = get_logger(config['log']['log_file'])
app = Flask("robot_backend")
app.register_blueprint(source_web)
app.register_blueprint(wechat_web)
app.register_blueprint(manage_web)

CORS(app, supports_credentials=True)
CORS(app, resources=r'/*')

@app.route("/test")
def test():
    judge_result = {
        'judge': True,
        'details': '12312321\n213213'
    }
    filter_result = json.dumps(judge_result, ensure_ascii=False)
    candidate_id = '111'
    job_id = 'jjj'
    prompt = 'sdfsdf'
    insert_filter_cache(candidate_id, job_id, prompt, filter_result)
    return "Hello, World!"





if __name__=="__main__":
    app.run(port=2040,host="0.0.0.0",debug=True)
