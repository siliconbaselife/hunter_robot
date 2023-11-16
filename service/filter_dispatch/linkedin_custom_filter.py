import json
from utils.config import config
from utils.log import get_logger
from algo.llm_inference import ChatGPT
from algo.llm_base_model import Prompt
logger = get_logger(config['log']['log_file'])


def linkedin_custom_filter(candidate_info, job_res):
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


    chatgpt = ChatGPT()
    prompt = Prompt(prompt_msg)
    result = chatgpt.chat(prompt)

    if 'B.不合适' in result:
        judge_ok = False
    else:
        judge_ok = True

    judge_result = {
        'judge': judge_ok,
        'details': result
    }
    return judge_result
