from dao.task_dao import query_account_type_db, is_chatting_db
from .filter_dispatch import *

__preprocess_dispatcher = {
    'boss': boss_preprocess
}

__filter_dispatcher = {
    'custom_service': common_custom_service_filter 
}

def preprocess(account_id, raw_candidate_info):
    platform_type = query_account_type_db(account_id)
    assert platform_type in __preprocess_dispatcher, f"unsupport platform type {platform_type} from account {account_id}"
    return __preprocess_dispatcher[platform_type](raw_candidate_info)

def candidate_filter(job_id, candidate_info):
    # job_requirement = query_job_requirement_db(job_id)
    if is_chatting_db(job_id, candidate_info['id']):
        return {'judge': False}
    return __filter_dispatcher['custom_service'](candidate_info)