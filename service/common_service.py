from utils.log import get_logger
from utils.config import config
from dao.tool_dao import get_configs_by_keys, upsert_config


logger = get_logger(config['log']['log_file'])


def get_configs(keys):
    logger.info(
        "[backend_tools] get_config by keys = {}".format(
            keys)
    )
    if (keys is None or len(keys) == 0):
        return {}
    
    return get_configs_by_keys(keys)

def update_config(key, value):
    logger.info(
        "[backend_tools] update_config by key = {}, value = {}".format(
            key, value)
    )
    if key is None:
        return None
    elif value is None:
        value = ""
    upsert_config(key, value)
    return None
