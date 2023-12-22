from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config
import time
logger = get_logger(config['log']['log_file'])

def maimai_preprocessor_v2(raw_candidate_info):
    try:
        exp = []
        for e in raw_candidate_info.get('exp', []):
            des = e["description"] or ''
            des = des.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            exp.append({
                "company":e["company"],
                "v":e["v"],
                "position":e["position"],
                "worktime":e["worktime"],
                "description":des
            })
        raw_candidate_info['exp'] = exp
        return raw_candidate_info

    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {raw_candidate_info} failed for {e}, {traceback.format_exc()}')
        return raw_candidate_info



