from utils.log import get_logger
from utils.config import config
from dao.tool_dao import get_configs_by_keys, upsert_config
import json


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
        "[backend_tools] update_config by key = %s, value = %s", 
        key, value
    )
    
    if key is None:
        return None
    
    # 确保 key 是字符串
    key = str(key)
    
    # 处理 value 类型
    if value is None:
        value = ""
    elif isinstance(value, (dict, list)):
        # 如果是字典或列表，转换为 JSON 字符串
        try:
            value = json.dumps(value, ensure_ascii=False)
        except Exception as e:
            logger.error("JSON 序列化失败: %s", e)
            value = str(value)
    
    try:
        upsert_config(key, value)
    except Exception as e:
        logger.error("更新配置失败: %s", e)
    
    return None