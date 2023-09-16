import json
import time
from utils.config import config
from utils.utils import is_211, is_985, get_degree_num, str_is_none
from utils.log import get_logger

logger = get_logger(config['log']['log_file'])


def maimai_autoload_filter(candidate_info, job_res):
    filter_args = json.loads(job_res[6])['filter_args']

    # ###
    # {
    #     'age_range':[18,35],
    #     'min_degree':'中专',
    #     'location':'北京',
    #     'job_tags':['客服','电话销售'],
    #      'school':2
    # }
    ###
    age_range = (filter_args['age_range'][0], filter_args['age_range'][1])
    min_degree = filter_args['min_degree']
    location = filter_args['location']
    job_tags =  filter_args['job_tags']
    active_threshold = int(filter_args['active_threshold']) * 60
    school_threshold = filter_args['school']

    

    is_active = (int(time.time()) - int(candidate_info['active_time'])) < active_threshold
    age_ok = candidate_info['age'] >= age_range[0] and candidate_info['age'] <= age_range[1]
    degree_ok = int(candidate_info['degree']) >= get_degree_num(min_degree)

    school_ok = False
    for edu in candidate_info['education']:
        if school_threshold == 2:
            if is_985(edu['school']):
                school_ok = True
        elif school_threshold == 1:
            if is_211(edu['school']):
                school_ok = True
        else:
            school_ok = True


    location_ok = False
    for l in location:
        if l in candidate_info['exp_location']:
            location_ok = True
        for e_r in candidate_info['exp_location_dict']["region"]:
            if l in e_r:
                location_ok = True  
        for e_c in  candidate_info['exp_location_dict']["cities"]:
            if l in e_c:
                location_ok = True  

    job_ok = True
    
    if 'job_tags' in filter_args and filter_args['job_tags'] != "":
        job_ok = False
        for jt in job_tags:
            if jt in candidate_info['major']:
                job_ok = True
            for w in candidate_info['work']:
                if jt in w['position']:
                    job_ok = True
            for ep in candidate_info['exp_positon_name']:
                if jt in ep:
                    job_ok = True

    neg_filter_ok = True
    if 'neg_words' in filter_args and filter_args['neg_words'] != "":
        neg_words = filter_args['neg_words']
        for n in neg_words:
            if str_is_none(n):
                continue
            for w in candidate_info['work']:
                if n in w['company']:
                    neg_filter_ok = False
           
    

    judge_result = {
        'judge': is_active and age_ok and degree_ok and location_ok and job_ok and school_ok and neg_filter_ok,
        'details': {
            'is_active': is_active,
            'age': age_ok,
            'degree': degree_ok,
            'location': location_ok,
            'job_position': job_ok,
            'school': school_ok,
            'neg_filter_ok':neg_filter_ok
        }
    }
    return judge_result
