from dao.task_dao import query_account_type_db, is_chatting_db
from .filter_dispatch import *
from utils.log import get_logger
from dao.task_dao import *
import json
logger = get_logger(config['log']['log_file'])
__preprocess_dispatcher = {
    'Boss': boss_preprocess
}

__filter_dispatcher = {
    'common_custom_service_filter': common_custom_service_filter, 
    'shijiazhuang_custom_service_filter': shijiazhuang_custom_service_filter
}

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