from dao.task_dao import query_account_type_db, is_chatting_db
from .filter_dispatch import *
from utils.log import get_logger
from dao.task_dao import *
import json
from threading import Lock
logger = get_logger(config['log']['log_file'])

__preprocess_dispatcher = {
    'Boss': boss_preprocess,
    'Linkedin': linkedin_preprocess,
    'maimai': maimai_preprocess
}

__filter_dispatcher = {
    'common_custom_service_filter': common_custom_service_filter, 
    'shijiazhuang_custom_service_filter': shijiazhuang_custom_service_filter,
    'shijiazhuang_qinggan_service_filter': shijiazhuang_qinggan_service_filter,
    'linkedin_common_service_filter': linkedin_common_service_filter,
    'nlp_maimai_service_filter': nlp_maimai_service_filter,
    'no_condition_common_filter': no_condition_common_filter,
    'maimai_autoload_filter': maimai_autoload_filter,
    'boss_autoload_filter': boss_autoload_filter,
    'linkedin_autoload_filter': linkedin_autoload_filter,
    'maimai_custom_filter': maimai_custom_filter,
    'linkedin_custom_filter':linkedin_custom_filter,
    'maimai_autoload_filter_v2':maimai_autoload_filter_v2,
    'linkedin_autoload_filter_v2':linkedin_autoload_filter_v2,
    'boss_autoload_filter_v2':boss_autoload_filter_v2,
    'liepin_autoload_filter_v2':liepin_autoload_filter_v2
}

__preprocess_dispatcher_v2 = {
    'Boss': boss_preprocess_v2,
    'Linkedin': linkedin_preprocessor_v2,
    'maimai': maimai_preprocessor_v2,
    'liepin':liepin_preprocessor_v2
}


_account_force_context = {}
_account_force_lock = Lock()
_account_force_thresh = 30

def judge_and_update_force(account_id, filter_result):
    global _account_force_context, _account_force_lock, _account_force_thresh
    to_touch_strategy = filter_result['judge']
    force_touch =False
    with _account_force_lock:
        if account_id not in _account_force_context:
            _account_force_context[account_id] = {
                'count': 1
            }
        _account_force_context[account_id]['count'] += 0 if to_touch_strategy else 1
        if to_touch_strategy:
            logger.info(f"judge_and_update_force: account {account_id} to strategy touch, count {_account_force_context[account_id]['count']} will clear")
            _account_force_context[account_id]['count'] = 0
        elif _account_force_context[account_id]['count'] >= _account_force_thresh:
            logger.info(f"judge_and_update_force: account {account_id} meet count thresh, count {_account_force_context[account_id]['count']} will force")
            _account_force_context[account_id]['count'] = 0
            force_touch = True
    if force_touch:
        filter_result['judge'] = True
    if 'details' not in filter_result:
        filter_result['details'] = {}
    filter_result['details']['force'] = force_touch
    return filter_result

def preprocess_v2(account_id, raw_candidate_info, platform_type):
    assert platform_type in __preprocess_dispatcher_v2, f"unsupport platform type {platform_type} from account {account_id}"
    return __preprocess_dispatcher_v2[platform_type](raw_candidate_info)

def preprocess(account_id, raw_candidate_info):
    platform_type = query_account_type_db(account_id)
    assert platform_type in __preprocess_dispatcher, f"unsupport platform type {platform_type} from account {account_id}"
    return __preprocess_dispatcher[platform_type](raw_candidate_info)

def candidate_filter(job_id, candidate_info):
    # job_requirement = query_job_requirement_db(job_id)
    #多账号去重
    if is_chatting_db(job_id, candidate_info['id']):
        return {'judge': False}
    
    job_res = get_job_by_id(job_id)
    if len(job_res) == 0:
        logger.info(f"candidate_filter: job config wrong, not exist: {job_id}, {candidate_info['id']}")
        
    filter_config = json.loads(job_res[0][6],strict=False)["filter_config"]
    return __filter_dispatcher[filter_config](candidate_info, job_res[0])