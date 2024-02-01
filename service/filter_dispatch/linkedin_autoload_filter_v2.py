import json
import time
from utils.config import config
from utils.utils import is_211, is_985, get_degree_num, str_is_none,get_degree_eng_dict
from utils.log import get_logger


def linkedin_autoload_filter_v2(raw_candidate_info, job_res):
    filter_args = json.loads(job_res[6])['dynamic_job_config']
    
    candidate_info = raw_candidate_info['profile']


    min_degree = filter_args['min_degree']
    
    c_json = json.dumps(candidate_info, ensure_ascii=False)
    edu_json = json.dumps(candidate_info.get('educations', []), ensure_ascii=False)
    language_json = json.dumps(candidate_info.get('languages', []), ensure_ascii=False)

    degree_list = get_degree_eng_dict(min_degree)

    degree_ok = False
    for d in degree_list:
        if d in edu_json:
            degree_ok = True

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
                for w in candidate_info.get('exp', []):
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
                for w in candidate_info.get('exp', []):
                    if c in w['company'] or w['company'] in c:
                        neg_company_ok = False
                for c_s in candidate_info['companies']:
                    if c_s in c or c in c_s:
                        neg_company_ok = False
    
    language_ok = True
    if 'languages' in filter_args and filter_args['languages'] != "":
        languages = []
        for e in filter_args['languages']:
            if not str_is_none(e):
                languages.append(e)
        if len(languages) > 0:
            for l in languages:
                if l not in language_json:
                    language_ok = False
                    break
            


    judge_result = {
        'judge':  degree_ok and neg_company_ok and neg_filter_ok and ex_company_ok and tag_ok and language_ok,
        'details': {
            'degree_ok': degree_ok,
            'neg_company_ok': neg_company_ok,
            'neg_filter_ok': neg_filter_ok,
            'ex_company_ok': ex_company_ok,
            'tag_ok':tag_ok,
            'language_ok':language_ok
        }
    }
    return judge_result