import json
import time
from utils.log import get_logger
from utils.config import config


logger = get_logger(config['log']['log_file'])

##这里没更新chat表的detail，是把所有的更新动作，放到了用户回复的时候去append
def get_msg(filter_result):
    ##主动来找且没给联系方式的
    if filter_result == 'NULL' or filter_result == None or filter_result == 'None':
        return "亲, 您对我们感兴趣的话, hr会跟您详细沟通, 方便交换个联系方式或者简历吗?"
    filter_dict = json.loads(filter_result)
    ##期望岗位相符的
    if filter_dict['details']['wish']:
        return "亲, 您的期望职位和我们岗位很相符呢，请问您方便交换个联系方式或者简历吗？"
    ##过往经验相符的
    if filter_dict['details']['experience']:
        return "亲，您的过往经验和我们岗位很相符呢，请问您方便交换个联系方式或者简历吗？"
    ##应该只有那部分force的会漏到这里
    return "亲，您方便交换个联系方式或者简历吗?"


def common_need_recall_filter(chat_info):
    candidate_id = chat_info[0]
    recall_msg = ""

    contact_unget = False
    reject_intent = False

    ##还没拿到简历或联系方式
    if chat_info[2] != 'NULL':
        contact_unget = True
    
    ##是否过程里已经有了拒绝意图
    if '拒绝' in str(chat_info[3]):
        reject_intent = True

    ##范围内的才进行召回
    time_match = (int(time.time()) - int(chat_info[5].timestamp())) > 86400 and  (int(time.time()) - int(chat_info[5].timestamp())) < 259200

    #召回几次后不再进行召回
    count_threshold = 2
    less_count = int(chat_info[6]) < count_threshold

    filter_result = chat_info[4]
    logger.info(f"candidate_recall,contact_unget: {contact_unget}, reject_intent:{reject_intent},time_match: {time_match}, less_count:{less_count}, filter_result:{filter_result}")
    if contact_unget and not reject_intent and time_match and less_count:
        recall_msg = get_msg(filter_result)
        ##todo 这里需要去更新一下chat表的聊天记录
        # append_msg(chat_info[3])
        res = {
            "candidate_id": candidate_id,
            "need_recall": True,
            "recall_msg": recall_msg
        }
        return True, res
    else:
        return False, None