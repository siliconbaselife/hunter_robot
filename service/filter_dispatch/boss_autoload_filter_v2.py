import json
from .utils import degree_compare
import time
from utils.utils import is_211, is_985, get_degree_num,str_is_none
from utils.log import get_logger
from utils.config import config


logger = get_logger(config['log']['log_file'])


def boss_autoload_filter_v2(candidate_info, job_res):
    filter_args = json.loads(job_res[6])['dynamic_job_config']

    age_range = (filter_args['min_age'], filter_args['max_age'])
    min_degree = filter_args['min_degree']
    school_threshold = filter_args['school']

    age = 0
    if candidate_info['geekCard']['ageDesc'] is not None and candidate_info['geekCard']['ageDesc'] != '':
        age = int(candidate_info['geekCard']['ageDesc'].split('岁'))

    age_ok = int(age) >= int(age_range[0]) and int(age) <= int(age_range[1])
    degree_ok = degree_compare(candidate_info['degree'], min_degree)


    school_threshold = filter_args['school']
    school_ok = False
    for edu in candidate_info['geekCard'].get('geekEdus', []):
        if school_threshold == 2:
            if is_985(edu['school']):
                school_ok = True
        elif school_threshold == 1:
            if is_211(edu['school']):
                school_ok = True
        else:
            school_ok = True

    c_json = json.dumps(candidate_info, ensure_ascii=False)

    tag_ok = True
    if 'job_tags' in filter_args and filter_args['job_tags'] != "":
        job_tags = []
        for j in filter_args['job_tags']:
            if not str_is_none(j):
                job_tags.append(j)
        if len(job_tags) > 0:
            tag_ok = False
            for jt in job_tags:
                if c_json in jt or jt in c_json:
                    tag_ok = True    
    
    ex_company_ok = True
    if 'ex_company' in filter_args and filter_args['ex_company'] != "":
        ex_company = []
        for e in filter_args['ex_company']:
            if not str_is_none(e):
                ex_company.append(e)
        if len(ex_company) > 0:
            ex_company_ok = False
            for c in ex_company:
                for w in candidate_info['geekCard'].get('geekWorks', []):
                    if c in w['company'] or w['company'] in c:
                        ex_company_ok = True
                for c_s in candidate_info['companies']:
                    if c_s in c or c in c_s:
                        ex_company_ok = True

    neg_filter_ok = True
    if 'neg_words' in filter_args and filter_args['neg_words'] != "":
        neg_words = []
        for j in filter_args['neg_words']:
            if not str_is_none(j):
                neg_words.append(j)
        if len(neg_words) > 0:
            for n in neg_words:
                if c_json in n or n in c_json:
                    neg_filter_ok = False
    

    neg_company_ok = True
    if 'neg_company' in filter_args and filter_args['neg_company'] != "":
        neg_company = []
        for e in filter_args['neg_company']:
            if not str_is_none(e):
                neg_company.append(e)
        if len(neg_company) > 0:
            for c in neg_company:
                for w in candidate_info['geekCard'].get('geekWorks', []):
                    if c in w['company'] or w['company'] in c:
                        neg_company_ok = False
                for c_s in candidate_info['companies']:
                    if c_s in c or c in c_s:
                        neg_company_ok = False

    judge_result = {
        'judge': age_ok and degree_ok and school_ok and neg_company_ok and neg_filter_ok and ex_company_ok and tag_ok,
        'details': {
            'age_ok': age_ok,
            'degree_ok': degree_ok,
            'school_ok': school_ok,
            'neg_company_ok': neg_company_ok,
            'neg_filter_ok': neg_filter_ok,
            'ex_company_ok': ex_company_ok,
            'tag_ok':tag_ok
        }
    }
    return judge_result

