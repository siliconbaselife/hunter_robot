from .utils import degree_compare
import time

def linkedin_common_service_filter(candidate_info, job_res):
    age_range = (18, 35)
    min_degree = '中专'
    location = '北京'
    job_tags = []

    # age_ok = candidate_info['age'] >= age_range[0] and candidate_info['age'] <= age_range[1]
    # degree_ok = degree_compare(candidate_info['degree'], min_degree)
    # location_ok = candidate_info['exp_location']==location
    exp_position = candidate_info['exp_position']
    # exp_salary = candidate_info['exp_salary']

    # if time.localtime().tm_hour > 6 and time.localtime().tm_hour < 23:
    #     threshold = 300
    # else:
    #     threshold = 21600
           
    # is_active = (int(time.time()) - int(candidate_info['active_time'])) < threshold


    # has_wish = False
    # for tag in job_tags:
    #     if tag in exp_position:
    #         has_wish = True
    #         break

    has_experience = False
    if len(job_tags) == 0:
        has_experience = True
    else:
        for t in job_tags:
            if t in exp_position:
                has_experience = True

    judge_result = {
        'judge': has_experience,
        'details': {
            # 'age': age_ok,
            # 'degree': degree_ok,
            # 'location': location_ok,
            'experience': has_experience
            # 'wish': has_wish,
            # 'is_active': is_active
        }
    }
    return judge_result