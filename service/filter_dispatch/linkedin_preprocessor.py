from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])

def linkedin_preprocess(raw_candidate_info):
    try:
        tmp = raw_candidate_info
        # cid = tmp['trackingUrn'].split(':')[-1]
        cid = tmp['id']
        cname = tmp['profile']['name']
        logger.info(f"test_name: {cname}")
        age = 0
        degree = ""
        active = ""
        if tmp['secondarySubtitle'] is not None:
            exp_location = tmp['secondarySubtitle']['text']
        else:
            exp_location = ""
        exp_salary = ""
        position_name = tmp['primarySubtitle']['text']
        active_time = ""


        work = []
        ## parse work
        if tmp['primarySubtitle'] != None:
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

        personal_desc = ''
        personal_summary = ''
        personal_url = ''
        languages = []
        education = []
        work = []

        if 'profile' in tmp and tmp['profile'] is not None:
            personal_desc = tmp['profile'].get('short_description', '')
            personal_summary = tmp['profile'].get('summary', '')
            personal_url = tmp['profile'].get('contactInfo', '').get('url', '')
            languages = tmp['profile'].get('languages', '')
            education = []
            work = []
            for e in tmp['profile'].get('educations', []):
                if e.get('majorInfo', '') == '':
                    sdegree = ''
                    department = ''
                else:
                    s_d = e.get('majorInfo', '').split(',')
                    if len(s_d) < 2:
                        sdegree = ''
                        department = ''
                    else:
                        sdegree = e.get('majorInfo', '').split(',')[0]
                        department = e.get('majorInfo', '').split(',')[1]

                if e.get('timeInfo', '') == '':
                    start_date_ym = ''
                    end_date_ym = ''
                else:
                    start_date_ym = e['timeInfo'].split('-')[0].strip()
                    end_date_ym = e['timeInfo'].split('-')[1].strip()

                education.append({
                    'school' : e.get('schoolName', ''),
                    'sdegree': sdegree,
                    'department': department,
                    'start_date_ym': start_date_ym,
                    'end_date_ym': end_date_ym
                })
            for e in tmp['profile'].get('experiences', []):
                workPosition = ''
                workDescription = ''
                for w in e['works']:
                    workPosition = workPosition + w.get('workPosition', '') + ','
                    workDescription = workDescription + w.get('workDescription', '') + ','
                work.append({
                    'company': e.get('companyName', ''),
                    'timeinfo': e.get('timeInfo', ''),
                    'locationInfo': e.get('locationInfo', ''),
                    'position':workPosition,
                    'description': workDescription
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
            'work': work,
            'active_time': active_time,
            'personal_desc': personal_desc,
            'personal_summary': personal_summary,
            'personal_url': personal_url,
            'languages': languages,
            'education': education,
            'work': work

        } 

    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {cid}, {cname} failed for {e}, {traceback.format_exc()}')
        with open(f'test/fail/{cid}_{cname}.json', 'w') as f:
            f.write(json.dumps(raw_candidate_info, indent=2, ensure_ascii=False))
        return {
            'id': "" if cid is None else cid,
            'name': "" if cname is None else cname,
            'age': 0 if age is None else age,
            'degree': "" if degree is None else degree,
            'active': "" if active is None else active,
            'exp_location': "" if exp_location is None else exp_location,
            'exp_salary': "" if exp_salary is None else exp_salary,
            'exp_position': "" if position_name is None else position_name,
            'education': "" if education is None else education,
            'work': "" if work is None else work,
            "active_time": "" if active_time is None else active_time
        }

    