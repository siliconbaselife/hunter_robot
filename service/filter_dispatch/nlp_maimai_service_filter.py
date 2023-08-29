from .utils import degree_compare
import time

from utils.config import config
from utils.utils import is_211
from utils.log import get_logger
logger = get_logger(config['log']['log_file'])

def nlp_maimai_service_filter(candidate_info):


####阈值
    
    # if time.localtime().tm_hour > 6 and time.localtime().tm_hour < 23:
    #     threshold = 10800
    # else:
    #     threshold = 86400
    threshold = 8640000

    age_range = (23, 32)
    min_degree = 2
    location = ['北京', 'beijing', 'Beijing']
    job_tags = ['算法工程师', '算法研究员', 'nlp', 'NLP', 'Nlp']
    

#####判定

    is_active = (int(time.time()) - int(candidate_info['active_time'])) < threshold
    age_ok = candidate_info['age'] >= age_range[0] and candidate_info['age'] <= age_range[1]
    degree_ok = int(candidate_info['degree']) >= min_degree


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

    school_ok = False
    for edu in candidate_info['education']:
        if is_211(edu['school']):
            school_ok = True
           
    

    judge_result = {
        'judge': is_active and age_ok and degree_ok and location_ok and job_ok and school_ok,
        'details': {
            'is_active': is_active,
            'age': age_ok,
            'degree': degree_ok,
            'location': location_ok,
            'job_position': job_ok,
            'school': school_ok
        }
    }
    return judge_result