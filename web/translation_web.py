from flask import Flask, Response, request
from flask import Blueprint
from utils.web_helper import get_web_res_suc_with_data, get_web_res_fail
from utils.decorator import web_exception_handler
from utils.log import get_logger
from utils.config import config

import json
import math

from tools.translation_tools import get_translation_tool

translation_web = Blueprint('translation_web', __name__, template_folder='templates')

logger = get_logger(config['log']['log_file'])

@translation_web.route("/backend/tools/trans", methods=['POST'])
@web_exception_handler
def translation_api():
    logger.info(f"translation request in: {request.json}")
    src_txt = request.json.get('src_txt', None)
    if src_txt == None:
        return Response(json.dumps(get_web_res_fail("src_txt 未指定"), ensure_ascii=False))
    src_lang = request.json.get('src_lang', None)
    if src_lang == None:
        return Response(json.dumps(get_web_res_fail("src_lang 未指定"), ensure_ascii=False))
    dst_lang = request.json.get('dst_lang', None)
    if dst_lang == None:
        return Response(json.dumps(get_web_res_fail("dst_lang 未指定"), ensure_ascii=False))

    dst_txt = get_translation_tool().run(src_txt=src_txt, src_lang=src_lang, dst_lang=dst_lang)
    return Response(json.dumps(get_web_res_suc_with_data(dst_txt), ensure_ascii=False))


