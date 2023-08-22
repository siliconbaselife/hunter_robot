from flask import Flask, Response, request
from flask import Blueprint
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math
import traceback
from datetime import datetime


logger = get_logger(config['log']['log_file'])

wechat_web = Blueprint('source_web', __name__, template_folder='templates')
