from utils.config import config
from utils.log import get_logger
logger = get_logger(config['log']['log_file'])

def no_condition_common_filter(candidate_info):
    judge_result = {
        'judge': True,
        'details': {   
        }
    }
    return judge_result