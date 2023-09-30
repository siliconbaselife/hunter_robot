import json
from .utils import degree_compare
import time
from utils.utils import is_211, is_985, get_degree_num,str_is_none


def boss_autoload_filter(candidate_info, job_res):

     # ###
    # {
    #     'age_range':[18,35],
    #     'min_degree':'中专',
    #     'location':'北京',
    #     'job_tags':['客服','电话销售'],
    #     'active_threshold':60
    # }
    ###

    filter_args = json.loads(job_res[6])['filter_args']
   
    age_range = (filter_args['age_range'][0], filter_args['age_range'][1])
    min_degree = filter_args['min_degree']
    location = filter_args['location']
    
    threshold = int(filter_args['active_threshold']) * 60
    school_threshold = filter_args['school']


    age_ok = candidate_info['age'] >= age_range[0] and candidate_info['age'] <= age_range[1]
    degree_ok = degree_compare(candidate_info['degree'], min_degree)


    

    location_ok = False
    for l in location:
        if l in candidate_info['exp_location']:
            location_ok = True
    exp_position = candidate_info['exp_position']

    if candidate_info['active'] == "刚刚活跃":
        is_active = True 
    else:
        is_active = False
    # is_active = (int(time.time()) - int(candidate_info['active_time'])) < threshold

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

    has_wish = True
    has_experience = True
    if 'job_tags' in filter_args and filter_args['job_tags'] != "":
        job_tags =  filter_args['job_tags']

        has_wish = False
        for tag in job_tags:
            if str_is_none(tag):
                continue
            if tag in exp_position:
                has_wish = True
                break

        has_experience = False
        for item in candidate_info['work']:
            if has_experience:
                break
            judge_str = item['position']+item['responsibility']+item['emphasis']+item.get('department', '')
            for tag in job_tags:
                if str_is_none(tag):
                    continue
                if tag in judge_str:
                    has_experience = True
                    break

    neg_filter_ok = True
    if 'neg_words' in filter_args and filter_args['neg_words'] != "":
        neg_words = filter_args['neg_words']
        for n in neg_words:
            if str_is_none(n):
                continue
            for w in candidate_info['work']:
                if n in w['company'] or w['company'] in n:
                    neg_filter_ok = False

    judge_result = {
        'judge': age_ok and degree_ok and location_ok and (has_experience or has_wish) and is_active and school_ok and neg_filter_ok,
        'details': {
            'age': age_ok,
            'degree': degree_ok,
            'location': location_ok,
            'experience': has_experience,
            'wish': has_wish,
            'is_active': is_active,
            "school": school_ok,
            "neg_filter_ok": neg_filter_ok
        }
    }
    return judge_result

