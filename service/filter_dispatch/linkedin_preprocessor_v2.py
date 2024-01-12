from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config
import time
logger = get_logger(config['log']['log_file'])

def linkedin_preprocessor_v2(raw_candidate_info):
    try:
        for e in raw_candidate_info.get('profile', {}).get('experiences', []):
            for w in e.get('works', []):
                if 'workPosition' in w:
                    workPosition = w.get('workPosition', '') or ''
                    w['workPosition'] = workPosition.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                if 'workDescription' in w:
                    workDescription = w['workDescription'] or ''
                    w['workDescription'] = workDescription.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "") 
        for edu in raw_candidate_info.get('profile', {}).get('educations', []):
            summary = edu.get('summary', '') or ''
            edu['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        summary = raw_candidate_info.get('profile', {}).get('summary', '') or ''
        raw_candidate_info['profile']['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        return raw_candidate_info
    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {raw_candidate_info} failed for {e}, {traceback.format_exc()}')
        return raw_candidate_info