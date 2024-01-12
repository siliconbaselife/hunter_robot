from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config
import time
logger = get_logger(config['log']['log_file'])

def linkedin_preprocessor_v2(p):
    try:
        for l in p.get('profile', {}).get('languages', []):
                language = l.get('language', '') or ''
                l['language'] = language.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                des = l.get('des', '') or ''
                l['des'] = des.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        for e in p.get('profile', {}).get('experiences', []):
            companyName = e.get('companyName', '') or ''
            e['companyName'] = companyName.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            for w in e.get('works', []):
                workTimeInfo = w.get('workTimeInfo', '') or ''
                w['workTimeInfo'] = workTimeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                workLocationInfo = w.get('workLocationInfo', '') or ''
                w['workLocationInfo'] = workLocationInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                workPosition = w.get('workPosition', '') or ''
                w['workPosition'] = workPosition.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                workDescription = w.get('workDescription', '') or ''
                w['workDescription'] = workDescription.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")  
        for edu in p.get('profile', {}).get('educations', []):
            summary = edu.get('summary', '') or ''
            edu['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            degreeInfo = edu.get('degreeInfo', '') or ''
            edu['degreeInfo'] = degreeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            majorInfo = edu.get('majorInfo', '') or ''
            edu['majorInfo'] = majorInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            timeInfo = edu.get('timeInfo', '') or ''
            edu['timeInfo'] = timeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            schoolName = edu.get('schoolName', '') or ''
            edu['schoolName'] = schoolName.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        summary = p.get('profile', {}).get('summary', '') or ''
        role = p.get('profile', {}).get('role', '') or ''
        location = p.get('profile', {}).get('location', '') or ''
        name = p.get('profile', {}).get('name', '') or ''
        contact_info = json.dumps(p.get('profile', {}).get('contactInfo', {}), ensure_ascii=False)
        p['profile']['contactInfo'] = contact_info.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        p['profile']['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        p['profile']['role'] = role.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        p['profile']['location'] = location.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        p['profile']['name'] = name.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
        return p
    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {p} failed for {e}, {traceback.format_exc()}')
        return p