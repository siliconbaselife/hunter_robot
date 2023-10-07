import json
import time
from utils.log import get_logger
from utils.config import config
from service.task_service import get_job_by_id_service

logger = get_logger(config['log']['log_file'])

def get_msg(filter_result, job_already_recall_count, job_id):
    recall_type = 'zp'
    job_config = json.loads(get_job_by_id_service(job_id)[0][6])
    if 'recall_config' in job_config:
        recall_type = job_config['recall_config']

    if recall_type == 'zp':
        if job_already_recall_count == 0:
            if filter_result == 'NULL' or filter_result == None or filter_result == 'None':
                return "哈喽 哈喽 不知道看到消息了么？最近是在忙？方便看到消息回复一下么？我们做这个领域挺多年了，相信可以给你更好的帮助"
            else:
                return "哈喽 哈喽 不知道看到消息了么？最近是在忙？方便看到消息回复一下么？我们做这个领域挺多年了，相信可以给你更好的帮助"
        elif job_already_recall_count == 1:
            return "hi 亲，您对我们感兴趣的话，方便交换个联系方式或者简历吗？咱们约个时间详细沟通一下，我可以给你分享客户详细的信息内容"
        elif job_already_recall_count == 2:
            return "哈喽 亲 看给你发消息一直没有回复，是不感兴趣？其实除了这个客户，我们还有其他Top公司的机会，我也可以给你分享行业信息，大家交个朋友，认识交流一下，多个朋友多条路，你觉得呢？"
    elif recall_type == 'bd':
        if job_already_recall_count == 0:
            return "Hi,亲. 最近还很忙吗？我这边是提供海外人力解决方案的公司，如果您需要帮忙，欢迎随时与我联系哦~"
        elif job_already_recall_count == 1:
            return "Hi,亲. 您对我的提议感兴趣吗？很期待跟您的进一步合作。"
        elif job_already_recall_count == 2:
            return "Hi,亲. 最近你们有需求吗，有需求的话我们聊一聊呢。"
    
    return "亲，方便交换个联系方式，咱们后续保持联系吗？"


def common_need_recall_filter(chat_info, flag):
    candidate_id = chat_info[0]
    candidate_name = chat_info[1]
    job_id = chat_info[7]
    recall_msg = ""

    contact_unget = False
    reject_intent = False

    ##还没拿到简历或联系方式
    if chat_info[2] == 'NULL' or chat_info[2] == None or chat_info[2] == 'None':
        contact_unget = True
    
    ##是否过程里已经有了拒绝意图 ? 思考一下是不是不用判断拒绝，还是要拿简历
    # if '拒绝' in str(chat_info[3]):
    #     reject_intent = True

    #召回几次后不再进行召回
    count_threshold = 3
    less_count = int(chat_info[6]) < count_threshold

    ##时间范围内的才进行召回
    already_recall_count = int(chat_info[6])
    if flag:
        time_match = True
    else:
        if already_recall_count < 2:
            time_match = (int(time.time()) - int(chat_info[5].timestamp())) > 86400 and (int(time.time()) - int(chat_info[5].timestamp())) < 259200
        else:
            time_match = (int(time.time()) - int(chat_info[5].timestamp())) > 172800 and (int(time.time()) - int(chat_info[5].timestamp())) < 604800

    filter_result = chat_info[4]
    logger.info(f"candidate_recall,{candidate_id},contact_unget: {contact_unget}, reject_intent:{reject_intent},time_match: {time_match}, less_count:{less_count}, filter_result:{filter_result}")
    if contact_unget and time_match and less_count:
        recall_msg = get_msg(filter_result, already_recall_count, job_id)
        res = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "job_id": job_id,
            "need_recall": True,
            "recall_msg": recall_msg
        }
        return True, res
    else:
        return False, None