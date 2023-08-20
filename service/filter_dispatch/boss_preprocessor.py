from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])
def boss_preprocess(raw_candidate_info):
    try:
        tmp = raw_candidate_info
        geek_card = tmp['geekCard']
        edu_experience = tmp['showEdus']
        work_experience= tmp['showWorks']

        ## parse base info\
        cid, cname, age_desc, degree = geek_card['geekId'], geek_card['geekName'], \
                                                    geek_card['ageDesc'], geek_card['geekDegree']
        age = int(age_desc[:-1])
        active = tmp['activeTimeDesc']

        ## parse expect
        exp_location = geek_card['expectLocationName']
        exp_salary = geek_card['salary']
        position_name = geek_card['expectPositionName']

        ##active_time
        active_time = geek_card['activeTime']

        ## parse edu info
        education = []
        for item in edu_experience:
            if item['degreeName']== degree:
                education.append({
                    'school': ensure_valid(item['school']),
                    'major': ensure_valid(item['major']),
                })
                break

        ## parse 
        work = []
        for item in work_experience:
            emphasis = ','.join(item['workEmphasisList']) if item['workEmphasisList'] is not None else ''
            work.append({
                'company': ensure_valid(item['company']),
                'position': ensure_valid(item['positionName']),
                'responsibility': ensure_valid(item['responsibility']),
                'emphasis': ensure_valid(emphasis),
                'start': ensure_valid(item['startDate']),
                'end': ensure_valid(item['endDate'])
            })
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
    