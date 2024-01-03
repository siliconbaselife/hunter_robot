from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])

def boss_preprocess_v2(raw_candidate_info):
    try:
        desc_content = raw_candidate_info['geekCard'].get('geekDesc', {}).get('content', '') or ''
        raw_candidate_info['geekCard']['geekDesc']['content'] = desc_content.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        resp = raw_candidate_info.get('geekLaskWork', {}).get('responsibility', '') or ''
        raw_candidate_info['geekLaskWork']['responsibility'] = resp.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        for edu in raw_candidate_info('showEdus',[]):
            desc = edu.get('eduDescription', '') or ''
            edu['eduDescription'] = desc.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        for work in raw_candidate_info('showWorks', []):
            resp = work.get('responsibility', '') or ''
            work['responsibility'] = resp.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        return raw_candidate_info
    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {raw_candidate_info} failed for {e}, {traceback.format_exc()}')
        return raw_candidate_info