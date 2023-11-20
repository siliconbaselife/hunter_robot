import json
from utils.config import config
from utils.log import get_logger
from algo.llm_inference import ChatGPT
from algo.llm_base_model import Prompt
logger = get_logger(config['log']['log_file'])

from dao.task_dao import insert_filter_cache, get_filter_cache, update_filter_cache
def maimai_custom_filter(candidate_info, job_res):
    custom_filter_content = json.loads(job_res[6])['custom_filter_content']
    


    if candidate_info['gender'] == 0:
        gender = '男'
    else:
        gender = '女'
    if candidate_info['degree'] == 2:
        sdegree = '硕士'
    elif candidate_info['degree'] == 3:
        sdegree = '博士'
    elif candidate_info['degree'] == 1:
        sdegree = '本科'
    else:
        sdegree = '未知'

    edu = ''
    for e in candidate_info['education']:
        edu = edu + '学校:' + e['school'] + ',学位:' + e['sdegree'] + ',' + e['start_date_ym'] + '至' + e['end_date_ym'] + ',专业:' + e['department'] + '\n'

    work = ''
    for w in candidate_info['work']:
        work = work + '公司:' + w['company'] + ',在职时间:' + w['timeinfo'] + ',工作地点相关:' + w['locationInfo'] + ',工作岗位:' + w['position'] + ',工作描述:' + w['description'] + '\n'

    candidate_msg= f'候选人个人信息如下：\n姓名:{candidate_info["name"]}\n性别:{gender} \n期望职位:{candidate_info["exp_positon_name"]}\n年龄：{candidate_info["age"]}\n最高学历:{sdegree}\n学校经历:\n{edu}工作经历:\n{work}'

    prefix = '你是一个猎头，请判断候选人是否符合招聘要求，答案必须在最后一行，并且单独一行，A.合适，B.不合适\n请给出具体原因和推理过程，结果以json形式表示\n'

    prompt_msg = prefix + candidate_msg + '\n招聘要求:\n' + custom_filter_content + '\n'

    need_update = False
    need_insert = False
    filter_cache = get_filter_cache(candidate_info['id'], job_res[0])
    if len(filter_cache) > 0:
        if filter_cache[0][2] == prompt_msg:
            logger.info(f"shot_filter_cache:{candidate_info['id']}, {job_res['id']}")
            return json.loads(filter_cache[0][3])
        else:
            need_update = True
    else:
        need_insert = True


    chatgpt = ChatGPT()
    prompt = Prompt()
    prompt.add_user_message(prompt_msg)
    result = chatgpt.chat(prompt)

    if 'B.不合适' in result:
        judge_ok = False
    else:
        judge_ok = True

    judge_result = {
        'judge': judge_ok,
        'details': result
    }
    if need_insert:
        insert_filter_cache(candidate_info['id'], job_res['id'], prompt, json.dumps(judge_result, ensure_ascii=False))
        logger.info(f"insert_filter_cache:{candidate_info['id']}, {job_res['id']}")
    if need_update:
        update_filter_cache(prompt, json.dumps(judge_result, ensure_ascii=False), candidate_info['id'], job_res['id'])
        logger.info(f"update_filter_cache:{candidate_info['id']}, {job_res['id']},old_prompt:{filter_cache[0][2]};new_prompt:{prompt}")
    return judge_result
