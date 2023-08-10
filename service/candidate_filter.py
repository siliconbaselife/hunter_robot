from dao.task_dao import query_account_type_db, is_chatting_db
from .filter_dispatch import *
from utils.log import get_logger
from dao.task_dao import *
import json
from threading import Lock
logger = get_logger(config['log']['log_file'])
__preprocess_dispatcher = {
    'Boss': boss_preprocess
}

__filter_dispatcher = {
    'common_custom_service_filter': common_custom_service_filter, 
    'shijiazhuang_custom_service_filter': shijiazhuang_custom_service_filter,
    'shijiazhuang_qinggan_service_filter': shijiazhuang_qinggan_service_filter
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


def preprocess(account_id, raw_candidate_info):
    platform_type = query_account_type_db(account_id)
    assert platform_type in __preprocess_dispatcher, f"unsupport platform type {platform_type} from account {account_id}"
    return __preprocess_dispatcher[platform_type](raw_candidate_info)

def candidate_filter(job_id, candidate_info):
    # job_requirement = query_job_requirement_db(job_id)
    if is_chatting_db(job_id, candidate_info['id']):
        return {'judge': False}
    ##todo要用job_id去取数据库配置
    ##这里用job_id取
    job_res = get_job_by_id(job_id)
    if len(job_res) == 0:
        logger.info(f"job config wrong, not exist: {job_id}, {candidate_info['id']}")
    filter_config = json.loads(job_res[0][6])["filter_config"]
    return __filter_dispatcher[filter_config](candidate_info)