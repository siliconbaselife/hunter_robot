import easyocr
import os
import fitz
from utils.log import get_logger
from utils.config import config
from algo.llm_inference import ChatGPT
from algo.llm_base_model import Prompt
import time
import requests
import sys
import docx
from dao.tool_dao import *
from io import StringIO
import csv
logger = get_logger(config['log']['log_file'])
reader = easyocr.Reader(['ch_sim','en']) # this needs to run only once to load the model into memory

file_path_prefix = './tmp/'

def generate_csv(res):

    io = StringIO()
    w = csv.writer(io)
    for r in res:
        file_name = os.path.basename(r['f_path'])
        l = [file_name, r['res'], r['remark']]
        w.writerow(l)
        yield io.getvalue()
        io.seek(0)
        io.truncate(0)


def imglist_to_text(img_url_list):
    res = ''
    for img in img_url_list:
        res += '\n' + reader.readtext(img)
    return res

def img_to_text(f_path):
    return reader.readtext(f_path)

def downloadFile(url):
    file_name = os.path.basename(url)
    responsepdf = requests.get(url)
    if responsepdf.status_code == 200:
        with open(file_path_prefix + file_name , "wb") as code:
            code.write(responsepdf.content)
        return True, file_path_prefix + file_name
    else:
        return False, ""

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
        for t in tables:
           for r in  t.rows:
               for c in r.cells:
                   if c.text.strip() != '':
                        result_str += ';' + c.text
        return True, result_str
    elif f_path.endswith('doc'):
        return False, "EXT_NOT_SUPPORT"
    else:
        return False, "EXT_NOT_SUPPORT"

def content_extract_and_filter(file_raw_data, jd):
    chatgpt = ChatGPT()

    ext_prompt_msg = '以下是候选人信息，请提取关键信息并结构化输出\n$$$\n' + file_raw_data + "\n$$$"
    ext_prompt = Prompt()
    ext_prompt.add_user_message(ext_prompt_msg)
    file_key_data = chatgpt.chat(ext_prompt)

    prefix = '你是一个猎头，请判断候选人是否符合招聘要求\n答案必须在最后一行，并且单独一行 A.合适，B.不合适。\n并同时给出具体原因和推理过程\n'
    candidate_msg = f'$$$\n候选人个人信息如下：{file_key_data}\n$$$\n'
    filter_prompt_msg = prefix + candidate_msg + '\n招聘要求:\n' + jd + '\n'
    filter_prompt = Prompt()
    filter_prompt.add_user_message(filter_prompt_msg)
    res = chatgpt.chat(filter_prompt)
    return res

def exec_filter_task(manage_account_id, file_list, jd):
    filter_result = []
    for f_path in file_list:
        flag, file_raw_data = content_transfer(f_path)
        if not flag:
            logger.info(f'file_ext_not_support, {manage_account_id}, {f_path}')
            filter_result.append({
                "f_path": f_path,
                "res": file_raw_data,
                "remark":""
            })

        single_filter_result = content_extract_and_filter(file_raw_data, jd)
        res = 'QUALIFIED' if 'A.合适' in single_filter_result else 'UNQUALIFIED'
        filter_result.append({
            "f_path": f_path,
            "res": res,
            "remark": single_filter_result
        })
    
    return filter_result

