import json
from .utils import degree_compare
import time
from utils.utils import is_211, is_985, get_degree_num


def linkedin_autoload_filter(candidate_info, job_res):

    exp_position = candidate_info['exp_position']
    filter_args = json.loads(job_res[6])['filter_args']

    job_tags =  filter_args['job_tags']

    
    if len(job_tags) == 0:
        job_ok = True
    else:
        job_ok = False
        for jt in job_tags:
            if jt in exp_position or exp_position in jt:
                job_ok = True

    neg_filter_ok = True
    if 'neg_words' in filter_args:
        neg_words = filter_args['neg_words']
        for n in neg_words:
            if n in exp_position or exp_position in n:
                neg_filter_ok = False

                    
    judge_result = {
        'judge': job_ok and neg_filter_ok,
        'details': {
            'job_ok': job_ok,
            'neg_filter_ok': neg_filter_ok
        }
    }
    return judge_result

