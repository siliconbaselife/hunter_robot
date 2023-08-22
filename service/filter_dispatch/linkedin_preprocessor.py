from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])

def linkedin_preprocess(raw_candidate_info):
    try:
        tmp = raw_candidate_info
        cid = tmp['trackingUrn'].split(':')[-1]
        cname = tmp['title']['text']
        logger.info(f"test_name: {cname}")
        age = ""
        degree = ""
        active = ""
        exp_location = tmp['secondarySubtitle']['text']
        exp_salary = ""
        position_name = tmp['primarySubtitle']['text']
        education = ""
        
        work = []
        ## parse work
        if '-' in tmp['primarySubtitle']['text']:
            strs = tmp['primarySubtitle']['text'].split('-')
            work.append({
                'company': strs[0].strip(),
                'position': strs[1].strip(),
                'responsibility': strs[1].strip(),
                'emphasis': "",
                'start': "",
                'end': ""
            })

        active_time = ""

        return {
            'id': cid,
            'name': cname,
            'age': age,
            'degree': degree,
            'active': active,
            'exp_location': exp_location,
            'exp_salary': exp_salary,
            'exp_position': position_name,
            'education': education,
            'work': work,
            "active_time": active_time
        } 

    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {cid}, {cname} failed for {e}, {traceback.format_exc()}')
        with open(f'test/fail/{cid}_{cname}.json', 'w') as f:
            f.write(json.dumps(raw_candidate_info, indent=2, ensure_ascii=False))
        return {
            'id': "" if cid is None else cid,
            'name': "" if cname is None else cname,
            'age': "" if age is None else age,
            'degree': "" if degree is None else degree,
            'active': "" if active is None else active,
            'exp_location': "" if exp_location is None else exp_location,
            'exp_salary': "" if exp_salary is None else exp_salary,
            'exp_position': "" if position_name is None else position_name,
            'education': "" if education is None else education,
            'work': "" if work is None else work,
            "active_time": "" if active_time is None else active_time
        }

    