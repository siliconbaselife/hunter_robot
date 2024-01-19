from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config
import time
logger = get_logger(config['log']['log_file'])

def liepin_preprocessor_v2(raw_candidate_info):
    try:
        refresh_time = raw_candidate_info.get('refreshTime','') or ''
        raw_candidate_info['refreshTime'] = refresh_time.replace('/', '')
        for p in raw_candidate_info.get('projectExpFormList', []):
            des = p.get('rpdDesc', '') or ''
            p['rpdDesc'] = des.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "").replace('/', '')
            duty = p.get('rpdDuty', '') or ''
            p['rpdDuty'] = duty.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "").replace('/', '')
        for w in raw_candidate_info.get('workExps', []):
            duty = w.get('rwDuty', '') or ''
            w['rwDuty'] = duty.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "").replace('/', '')
        return raw_candidate_info
    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {raw_candidate_info} failed for {e}, {traceback.format_exc()}')
        return raw_candidate_info



