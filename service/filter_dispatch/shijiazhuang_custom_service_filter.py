from .utils import degree_compare
import time

from utils.config import config
from utils.log import get_logger
logger = get_logger(config['log']['log_file'])

def shijiazhuang_custom_service_filter(candidate_info):
    age_range = (18, 35)
    min_degree = '中专'
    location = '石家庄'
    job_tags = ['客服','电话销售']

    age_ok = candidate_info['age'] >= age_range[0] and candidate_info['age'] <= age_range[1]
    degree_ok = degree_compare(candidate_info['degree'], min_degree)
    location_ok = candidate_info['exp_location']==location
    exp_position = candidate_info['exp_position']
    exp_salary = candidate_info['exp_salary']

    # ##3min以内打招呼
    # is_active = (int(time.time()) - int(candidate_info['active_time'])) < 180
    is_active = (int(time.time()) - int(candidate_info['active_time'])) < 21600


    has_wish = False
    for tag in job_tags:
        if tag in exp_position:
            has_wish = True
            break

    has_experience = False
    for item in candidate_info['work']:
        if has_experience:
            break
        logger.info(item['position'], item['responsibility'], item['emphasis'], item.get('department', ''))
        judge_str = item['position']+item['responsibility']+item['emphasis']+item.get('department', '')
        for tag in job_tags:
            if tag in judge_str:
                has_experience = True
                break

    judge_result = {
        'judge': age_ok and degree_ok and location_ok and (has_experience or has_wish) and is_active,
        'details': {
            'age': age_ok,
            'degree': degree_ok,
            'location': location_ok,
            'experience': has_experience,
            'wish': has_wish,
            'is_active': is_active
        }
    }
    return judge_result