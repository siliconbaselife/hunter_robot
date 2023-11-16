from flask import Flask
from utils.log import get_logger
from flask_cors import *
from web.source_web import source_web
from web.wechat_web import wechat_web
from web.manage_web import manage_web
from utils.config import config

logger = get_logger(config['log']['log_file'])
app = Flask("robot_backend")
app.register_blueprint(source_web)
app.register_blueprint(wechat_web)
app.register_blueprint(manage_web)

CORS(app, supports_credentials=True)
CORS(app, resources=r'/*')

@app.route("/test")
def test():
    return "Hello, World!"





if __name__=="__main__":
    app.run(port=2040,host="0.0.0.0",debug=True)
