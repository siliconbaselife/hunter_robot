import easyocr
import os
import fitz
from utils.log import get_logger
from utils.config import config
from algo.llm_inference import gpt_manager
from algo.llm_base_model import Prompt
import time
import requests
import sys
import docx
import traceback
from dao.tool_dao import *
from io import StringIO
import csv
logger = get_logger(config['log']['log_file'])
reader = easyocr.Reader(['ch_sim','en']) # this needs to run only once to load the model into memory

file_path_prefix = '/home/human/workspace/hunter_robot.v2.0/tmp/'

def get_candidate_id(profile, platform):
    if platform == 'maimai':
        return profile['id']
    if platform == 'Linkedin':
        return profile['id']
    if platform == 'Boss':
        return profile['geekCard']['geekId']

def generate_resume_csv(manage_account_id, platform, start_date, end_date):
    res = get_resume_by_filter(manage_account_id, platform, start_date, end_date)
    io = StringIO()
    w = csv.writer(io)

    l = ['候选人ID', '平台', '创建时间', '候选人姓名','地区','性别','工作总时长', '在职公司', '岗位', '最高学历', '专业', '历史公司', '毕业院校', '教育经历', '工作经历', '预期职位', '预期地点', '预期薪水', '其他倾向', '简历标签']
    w.writerow(l)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for r in res:
        try:
            candidate_id = r[1]
            platform = r[3]
            create_time = r[4].strftime("%Y-%m-%d %H:%M:%S")
            profile_json = r[5].replace('\n', ',')
            profile_json = profile_json.replace('/', '_')
            profile_json = profile_json.replace('，', ',')
            profile_json = profile_json.replace('u0000', ',')
            profile_json = profile_json.replace('\\', ',')
            profile = json.loads(profile_json, strict=False)

            # logger.info(f'download_resume_error_json, {candidate_id}, {e}, {e.args}, {traceback.format_exc()}')
            candidate_name = profile.get('name', '')
            region = profile.get('city', '')
            gender = profile.get('gender', '')
            work_time = profile.get('work_time', '')
            company = profile.get('company', '')
            position = profile.get('position', '')
            sdegree = profile.get('sdegree', '')
            major = profile.get('major', '')
            large_comps = profile.get('large_comps', '')
            school = profile.get('school', '')
            schools = ''
            for s in profile.get('edu', []):
                schools = schools + s.get('school', '') + ',' + s.get('department', '') + ',' + s.get('sdegree', '') + ',' + s.get('v', '') + '\n'
            if 'current_company' in profile:
                work_detail = profile['current_company'].get('company', '') + ',' + profile['current_company'].get('position', '') + ',' + profile['current_company'].get('worktime', '') + '\n'
            else:
                work_detail = ''
            for e in profile.get('exp', []):
                des = e.get('description', '') or ''
                work_detail = work_detail +','+ e.get('company', '') + ',' + e.get('position', '') + ',' + e.get('worktime', '') + ',' + e.get('v', '') + ',' + des + '\n'
            
            exp_positon = ','.join(profile['job_preferences'].get('positons', []))
            exp_location = ','.join(profile['job_preferences'].get('province_cities', []))
            exp_salary = profile['job_preferences'].get('salary', '')
            exp_prefer = ','.join(profile['job_preferences'].get('prefessions', []))
            tags = ','.join(profile.get('tag_list', []))
            l = [candidate_id, platform, create_time, candidate_name, region,gender,work_time, company, position, sdegree, major, large_comps, school, schools, work_detail, exp_positon, exp_location, exp_salary, exp_prefer, tags]
            w.writerow(l)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'download_resume_error3,{profile_json}')
            logger.info(f'download_resume_error3,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')



def generate_csv(res):
    s = res[0][6].replace('\n', '\\n')
    res_l = json.loads(s)
    io = StringIO()
    w = csv.writer(io)
    for r in res_l:
        file_name = os.path.basename(r['f_path'])
        l = [file_name, r['res'], r['remark']]
        w.writerow(l)
        yield io.getvalue()
        io.seek(0)
        io.truncate(0)


def imglist_to_text(img_url_list):
    res = ''
    for img in img_url_list:
        res = res + img_to_text(img)
    return res

def img_to_text(f_path):
    res = reader.readtext(f_path)
    s = ''
    for r in res:
        s = s + r[1] + '\n'
    return s

def downloadFile(url):
    file_name = os.path.basename(url)
    responsepdf = requests.get(url)
    if responsepdf.status_code == 200:
        with open(file_path_prefix + file_name , "wb") as code:
            code.write(responsepdf.content)
        return True, file_path_prefix + file_name, file_name
    else:
        return False, "", file_name

def content_transfer(f_path):
    file_name = os.path.basename(f_path)
    if f_path.endswith('jpg') or f_path.endswith('jpeg') or f_path.endswith('png'):
        return True, img_to_text(f_path)
    elif f_path.endswith('pdf'):
        final_url_list = []
        pdf = fitz.open(f_path)
        for page in pdf:
            mat=fitz.Matrix(10,10)
            pix = page.get_pixmap(matrix=mat)
            png_file_name = f"{file_name.split('.')[0]}-page-{page.number}.png"
            pix.save(png_file_name)
            final_url_list.append(png_file_name)
        pdf.close()
        res = imglist_to_text(final_url_list)
        for u in final_url_list:
            os.remove(u)
        return True, res
    elif f_path.endswith('docx'):
        f = docx.Document(f_path)
        result_str = ''
        for p in f.paragraphs:
            if p.text.strip() != '':
                result_str += ';' + p.text
        tables = f.tables
        last_cell = ''
        for t in tables:
           for r in  t.rows:
               for c in r.cells:
                   s = c.text.strip()
                   if s != '' and s != last_cell:
                        result_str += ';' + s
                        last_cell = s
        return True, result_str
    elif f_path.endswith('doc'):
        return False, "EXT_NOT_SUPPORT"
    else:
        return False, "EXT_NOT_SUPPORT"

def content_extract_and_filter(file_raw_data, jd):
    # chatgpt = ChatGPT()
    #先做个人为截断，如果有问题再说
    ext_prompt_msg = '以下是候选人信息，请提取关键信息并结构化输出\n$$$\n' + file_raw_data[0:3500] + "\n$$$"
    ext_prompt = Prompt()
    ext_prompt.add_user_message(ext_prompt_msg)
    file_key_data = gpt_manager.chat_task(ext_prompt)
    # file_key_data = chatgpt.chat(ext_prompt)
    logger.info(f"filter_task_content_extract_and_filter_file_key_data: {file_key_data}")
    prefix = '你是一个猎头，请判断候选人是否符合招聘要求\n给出具体原因和推理过程\n答案必须在最后一行，并且单独一行 A.合适，B.不合适'
    candidate_msg = f'$$$\n候选人个人信息如下：{file_key_data}\n$$$\n'
    filter_prompt_msg = prefix + candidate_msg + '\n招聘要求:\n' + jd + '\n'
    filter_prompt = Prompt()
    filter_prompt.add_user_message(filter_prompt_msg)
    res = gpt_manager.chat_task(filter_prompt)
    # res = chatgpt.chat(filter_prompt)
    return res

def exec_filter_task(manage_account_id, file_list, jd):
    filter_result = []
    for f_path in file_list:
        flag, file_raw_data = content_transfer(f_path)
        logger.info(f"filter_task_content_transfer:{f_path}, {flag}, {len(file_raw_data)}, {file_raw_data[0:3500]}")
        if not flag:
            logger.info(f'file_ext_not_support, {manage_account_id}, {f_path}')
            filter_result.append({
                "f_path": f_path,
                "res": file_raw_data,
                "remark":""
            })
            continue

        single_filter_result = content_extract_and_filter(file_raw_data, jd)
        logger.info(f"filter_task_content_extract_and_filter:{f_path}, {single_filter_result}")
        res = 'QUALIFIED' if 'A.合适' in single_filter_result else 'UNQUALIFIED'
        filter_result.append({
            "f_path": f_path,
            "res": res,
            "remark": single_filter_result
        })
    
    return filter_result

