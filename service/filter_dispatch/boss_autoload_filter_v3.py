import json
from .utils import degree_compare_v2
import time
from utils.utils import is_211, is_985, get_degree_num, str_is_none
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])


def fetch_geek_card(candidate_info):
    card = candidate_info["geekCard"]
    del card["positionName"]
    del card["interactDesc"]
    del card["feedback"]
    card_json = json.dumps(card, ensure_ascii=False)



    return card_json


def boss_autoload_filter_v3(candidate_info, job_res):
    filter_args = json.loads(job_res[6])['dynamic_job_config']

    age_range = (int(filter_args['min_age']), int(filter_args['max_age']))
    min_degree = filter_args['min_degree']
    school_threshold = filter_args['school']

    age = 0
    if candidate_info['geekCard']['ageDesc'] is not None and candidate_info['geekCard']['ageDesc'] != '':
        age = int(candidate_info['geekCard']['ageDesc'].split('岁')[0])

    age_ok = int(age) >= int(age_range[0]) and int(age) <= int(age_range[1])
    degree_ok = degree_compare_v2(candidate_info['geekCard']['geekDegree'], min_degree)

    ## 岗位filter TODO expect_jobs 增加到job_config
    expect_job = candidate_info['geekCard']['expectPositionName']
    expect_job_ok = expect_job in filter_args['expect_jobs']

    ## 薪酬filter TODO 明确单位：boss 月薪，min_salary和max_salary需要加到job_config
    pay_range = (int(filter_args['min_salary']), int(filter_args['max_salary']))
    if 'lowSalary' in candidate_info['geekCard'] and 'highSalary' in candidate_info['geekCard']:
        expect_range = (int(candidate_info['geekCard']['lowSalary']), int(candidate_info['geekCard']['highSalary']))
        pay_ok = pay_range[1] > expect_range[0]
    else:
        pay_ok = True

    ## 位置filter TODO 模糊匹配调试，location需要加到job_config
    expect_loc = {'name': candidate_info['geekCard']['expectLocationName'],
                  'code': candidate_info['geekCard']['expectLocationCode'] if 'expectLocationCode' in candidate_info[
                      'geekCard'] else candidate_info['geekCard']['expectLocation'],
                  'sub': candidate_info['geekCard']['expectSubLocationName'] if 'expectSubLocationName' in
                                                                                candidate_info['geekCard'] else None}
    offer_loc_list = filter_args['location']
    loc_ok = expect_loc['name'] in offer_loc_list

    ## 状态filter TODO status 需要增加到job_config
    apply_status = {'status': candidate_info['geekCard']['applyStatus'],
                    'desc': candidate_info['geekCard']['applyStatusDesc']}
    need_status_list = filter_args['status']
    status_ok = str(apply_status['status']) in need_status_list

    school_threshold = int(filter_args['school'])
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
    card_json = fetch_geek_card(candidate_info)

    tag_ok = True
    if 'job_tags' in filter_args and filter_args['job_tags'] != "":
        job_tags = []
        for j in filter_args['job_tags']:
            if not str_is_none(j):
                job_tags.append(j)
        if len(job_tags) > 0:
            tag_ok = False
            for jt in job_tags:
                if card_json in jt or jt in card_json:
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
                # for c_s in candidate_info['companies']:
                #     if c_s in c or c in c_s:
                #         ex_company_ok = True

    neg_filter_ok = True
    if 'neg_words' in filter_args and filter_args['neg_words'] != "":
        neg_words = []
        for j in filter_args['neg_words']:
            if not str_is_none(j):
                neg_words.append(j)
        if len(neg_words) > 0:
            for n in neg_words:
                if card_json in n or n in card_json:
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
                # for c_s in candidate_info['companies']:
                #     if c_s in c or c in c_s:
                #         neg_company_ok = False

    judge_result = {
        'judge': age_ok and degree_ok and school_ok and neg_company_ok and neg_filter_ok and ex_company_ok and tag_ok,
        'details': {
            'age_ok': age_ok,
            'degree_ok': degree_ok,
            'school_ok': school_ok,
            'neg_company_ok': neg_company_ok,
            'neg_filter_ok': neg_filter_ok,
            'ex_company_ok': ex_company_ok,
            'tag_ok': tag_ok,
            'expect_job_ok': expect_job_ok,
            'pay_ok': pay_ok,
            'loc_ok': loc_ok,
            'status_ok': status_ok,
        }
    }
    return judge_result
