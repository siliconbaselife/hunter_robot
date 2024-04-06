import easyocr
import os
import fitz
from utils.log import get_logger
from utils.config import config
from algo.llm_inference import gpt_manager
from algo.llm_base_model import Prompt
import time
import datetime
import requests
import sys
import docx
import traceback
from dao.tool_dao import *
from io import StringIO
import csv
import codecs
from flask_admin._compat import csv_encode
from dao.task_dao import get_chats_by_job_id_with_date,query_candidate_by_id
from dao.manage_dao import get_job_name_by_id
import json5
import re
from os.path import basename

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
    if platform == 'liepin':
        return profile['usercIdEncode']

def maimai_online_resume_upload_processor(manage_account_id, profile, platform):
    count = 0
    for p in profile:
        candidate_id = get_candidate_id(p, platform)
        if candidate_id == None or candidate_id == '':
            continue
        if len(get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id)) == 0:
            exp = []
            for e in p.get('exp', []):
                des = e["description"] or ''
                des = des.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                exp.append({
                    "company":e["company"],
                    "v":e["v"],
                    "position":e["position"],
                    "worktime":e["worktime"],
                    "description":des
                })
            p['exp'] = exp
            upload_online_profile(manage_account_id, platform, json.dumps(p, ensure_ascii=False), candidate_id)
            count = count + 1
    return count

def linkedin_online_resume_upload_processor(manage_account_id, profile, platform, list_name, min_age, max_age):
    count = 0
    for p in profile:
        candidate_id = get_candidate_id(p, platform)
        if list_name != '':
            add_list_relation(manage_account_id, list_name, candidate_id)
        if candidate_id == None or candidate_id == '':
            continue
        firt_work_year = 10000
        current_year = int(datetime.datetime.now().year)
        if len(get_resume_by_candidate_id_and_platform(candidate_id, platform, manage_account_id)) == 0 and 'profile' in p:
            for l in p.get('profile', {}).get('languages', []):
                language = l.get('language', '') or ''
                l['language'] = language.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                des = l.get('des', '') or ''
                l['des'] = des.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            for e in p.get('profile', {}).get('experiences', []):
                companyName = e.get('companyName', '') or ''
                e['companyName'] = companyName.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                for w in e.get('works', []):
                    workTimeInfo = w.get('workTimeInfo', '') or ''
                    w['workTimeInfo'] = workTimeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                    #截年龄
                    years = re.findall(r'\b\d{4}\b', w['workTimeInfo'])
                    min_year = 10000 if len(years) == 0 else int(min(years))
                    if min_year < firt_work_year:
                        firt_work_year = min_year
                    workLocationInfo = w.get('workLocationInfo', '') or ''
                    w['workLocationInfo'] = workLocationInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                    workPosition = w.get('workPosition', '') or ''
                    w['workPosition'] = workPosition.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                    workDescription = w.get('workDescription', '') or ''
                    w['workDescription'] = workDescription.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")  
            for edu in p.get('profile', {}).get('educations', []):
                summary = edu.get('summary', '') or ''
                edu['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                degreeInfo = edu.get('degreeInfo', '') or ''
                edu['degreeInfo'] = degreeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                majorInfo = edu.get('majorInfo', '') or ''
                edu['majorInfo'] = majorInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                timeInfo = edu.get('timeInfo', '') or ''
                edu['timeInfo'] = timeInfo.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
                #截年龄
                years = re.findall(r'\b\d{4}\b', edu['timeInfo'])
                max_year = 10000 if len(years) == 0 else int(max(years))
                if max_year < firt_work_year:
                    firt_work_year = max_year
                schoolName = edu.get('schoolName', '') or ''
                edu['schoolName'] = schoolName.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            age = current_year - firt_work_year + 23
            if min_age > age or max_age < age:
                logger.info(f'profile_age_filter：{manage_account_id}, {candidate_id}, {age}')
                continue

            summary = p.get('profile', {}).get('summary', '') or ''
            role = p.get('profile', {}).get('role', '') or ''
            location = p.get('profile', {}).get('location', '') or ''
            name = p.get('profile', {}).get('name', '') or ''

            url = p.get('profile', {}).get('contactInfo', {}).get("url", "") or ''
            p['profile']['contactInfo']["url"] = url.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            phone = p.get('profile', {}).get('contactInfo', {}).get("Phone", "") or ''
            p['profile']['contactInfo']["Phone"] = phone.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            email = p.get('profile', {}).get('contactInfo', {}).get("Email", "") or ''
            p['profile']['contactInfo']["Email"] = email.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")

            p['profile']['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['role'] = role.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['location'] = location.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['name'] = name.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            upload_online_profile(manage_account_id, platform, json.dumps(p, ensure_ascii=False), candidate_id)
            count = count + 1
    return count

def generate_candidate_csv_by_job_liepin(job_id, start_date, end_date):
    chat_list = get_chats_by_job_id_with_date(job_id, start_date, end_date)
    job_name = get_job_name_by_id(job_id)
    io = StringIO()
    w = csv.writer(io)

    l = ['岗位名称','候选人ID', '创建时间', '候选人姓名','来源','微信','电话','简历','对话详情','性别', '生日年份', '工作年限', '岗位', '学历', '地点', '薪资', '学校经历', '工作经历']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for c in chat_list:
        try:
            candidate_info = query_candidate_by_id(c[2])
            job_name = job_name
            candidate_id = c[2]
            create_time = c[9].strftime("%Y-%m-%d %H:%M:%S")
            candidate_name = c[3]
            if c[4] == 'user_ask':
                source = '候选人主动'
            elif c[4] == 'search':
                source= '机器人打招呼'
            else:
                source = '未知'
            if c[6] is None :
                wechat = ''
                phone = ''
                resume = ''
            else:
                try:
                    contact = json.loads(c[6])
                    wechat = contact['wechat'] or ''
                    phone = contact['phone'] or ''
                    resume = contact['cv'] or ''
                except Exception as e:
                    wechat = ''
                    phone = ''
                    resume = ''
                    logger.info(f'exception_filter:{candidate_id}, {candidate_name}, {c[6]}, {contact}, {e}, {e.args}, {traceback.format_exc()}')
            try:
                conversation = json.loads(c[7])
                con_str = ''
                for c in conversation:
                    con_str = con_str + c['speaker'] + ':' + c['msg'] + '\n'
            except Exception as e:
                con_str = ''

            if len(candidate_info) == 0:
                logger.info(f"chat_candidate_not_match, {candidate_id}")
                gender = ''
                born_year = ''
                work_year = ''
                position = ''
                degree = ''
                location = ''
                salary = ''
                edu = ''
                work = ''
            else:
                c_j = candidate_info[0][7].replace('\n','.')
                c_j = c_j.replace("\'", '\"')
                candidate_json = json.loads(c_j, strict=False)
                gender = candidate_json.get('basicInfoForm', {}).get('sex', '')
                born_year = candidate_json.get('simpleResumeForm', {}).get('resBirthYear', '')
                work_year = candidate_json.get('basicInfoForm', {}).get('workYearsDescr', '')
                position = candidate_json.get('basicInfoForm', {}).get('resTitle', '')
                degree = candidate_json.get('basicInfoForm', {}).get('eduLevelName', '')
                location = candidate_json.get('basicInfoForm', {}).get('dqName', '')
                salary = candidate_json.get('basicInfoForm', {}).get('salary', '')
                edu = ''
                for e in candidate_json.get('eduExpFormList', []):
                    edu = edu + str(e.get('startYear', '')) + '-' + str(e.get('endYear', ''))  + ', ' +  str(e.get('redDegreeName', '')) + ', ' +  str(e.get('redSchool', '')) + ', ' + str(e.get('redSpecial', '')) + '\n\n'
                work = ''
                for wo in candidate_json.get('workExps', []):
                    work = work + str(wo.get('startYear', '')) + '-' + str(wo.get('endYear', '')) + ', ' + str(wo.get('rwCompname', '')) + ', ' + str(wo.get('rwDqName', '')) + '\n' + str(wo.get('rwDuty', '')) + '\n\n'

            l = [job_id, candidate_id, create_time, candidate_name, source, wechat, phone, resume, con_str, gender, born_year, work_year, position, degree, location, salary, edu, work]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'test_download_candidate_liepin_error4, {c_j}')
            logger.info(f'test_download_candidate_liepin_error4,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

def generate_candidate_csv_by_job_Boss(job_id, start_date, end_date):
    chat_list = get_chats_by_job_id_with_date(job_id, start_date, end_date)
    job_name = get_job_name_by_id(job_id)
    io = StringIO()
    w = csv.writer(io)

    l = ['岗位名称','候选人ID', '创建时间', '候选人姓名','来源','微信','电话','简历','对话详情','薪资范围', '年龄', '最高学历', '性别', '状态', '学校', '教育经历', '工作经历']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for c in chat_list:
        try:
            candidate_info = query_candidate_by_id(c[2])
            job_name = job_name
            candidate_id = c[2]
            create_time = c[9].strftime("%Y-%m-%d %H:%M:%S")
            candidate_name = c[3]
            if c[4] == 'user_ask':
                source = '候选人主动'
            elif c[4] == 'search':
                source= '机器人打招呼'
            else:
                source = '未知'
            if c[6] is None :
                wechat = ''
                phone = ''
                resume = ''
            else:
                try:
                    contact = json.loads(c[6])
                    wechat = contact['wechat'] or ''
                    phone = contact['phone'] or ''
                    resume = contact['cv'] or ''
                except Exception as e:
                    wechat = ''
                    phone = ''
                    resume = ''
                    logger.info(f'exception_filter:{candidate_id}, {candidate_name}, {c[6]}, {contact}, {e}, {e.args}, {traceback.format_exc()}')
            try:
                conversation = json.loads(c[7])
                con_str = ''
                for c in conversation:
                    con_str = con_str + c['speaker'] + ':' + c['msg'] + '\n'
            except Exception as e:
                con_str = ''

            if len(candidate_info) == 0:
                logger.info(f"chat_candidate_not_match, {candidate_id}")
                salary = ''
                age = ''
                degree = ''
                gender = ''
                status = ''
                school = ''
                edu = ''
                work = ''
            else:
                c_j = candidate_info[0][7].replace('\n','.')
                c_j = c_j.replace("\'", '\"')
                candidate_json = json.loads(c_j, strict=False)
                salary = candidate_json.get('geekCard', {}).get('salary', '')
                age = candidate_json.get('geekCard', {}).get('ageDesc', '')
                degree = candidate_json.get('geekCard', {}).get('geekDegree', '')
                gender = candidate_json.get('geekCard', {}).get('geekGender', '')
                status = candidate_json.get('geekCard', {}).get('applyStatusDesc', '')
                school = candidate_json.get('geekCard', {}).get('geekEdu', {}).get('school', '')
                edu = ''
                for s in candidate_json.get('geekCard', {}).get('geekEdus', []):
                    edu = edu + s.get('school', '') or '' + ',' + s.get('major', '') or '' + ',' + s.get('degreeName', '') or '' + '\n' + s.get('startDate', '') or '' + '-' + s.get('endDate', '') or '' + '\n\n'
                work = ''
                for e in candidate_json.get('geekCard', {}).get('geekWorks', []):
                    work = work + e.get('company', '') or '' + ',' + e.get('workTime', '') or '' + ',' + e.get('positionName', '') or ''  + '\n'
                    work = work + e.get('startDate', '') or '' + '-' + e.get('endDate', '') or '' + '\n'
                    work = work + e.get('responsibility', '') or '' + '\n\n'
                    
            l = [job_id, candidate_id, create_time, candidate_name, source, wechat, phone, resume, con_str, salary, age, degree, gender, status, school, edu, work]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'test_download_candidate_boss_error4, {c_j}')
            logger.info(f'test_download_candidate_boss_error4,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

def generate_candidate_csv_by_job_Linkedin(job_id, start_date, end_date):
    chat_list = get_chats_by_job_id_with_date(job_id, start_date, end_date)
    job_name = get_job_name_by_id(job_id)
    io = StringIO()
    w = csv.writer(io)

    l = ['岗位名称','候选人ID', '创建时间', '候选人姓名','来源','微信','电话','邮箱','简历','对话详情','地区','岗位', '学校经历', '公司经历', '语言能力']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for c in chat_list:
        try:
            candidate_info = query_candidate_by_id(c[2])
            job_name = job_name
            candidate_id = c[2]
            create_time = c[9].strftime("%Y-%m-%d %H:%M:%S")
            candidate_name = c[3]
            if c[4] == 'user_ask':
                source = '候选人主动'
            elif c[4] == 'search':
                source= '机器人打招呼'
            else:
                source = '未知'
            if c[6] is None :
                wechat = ''
                phone = ''
                resume = ''
                email = ''
            else:
                try:
                    contact = json.loads(c[6])
                    wechat = contact['wechat'] or ''
                    phone = contact['phone'] or ''
                    resume = contact['cv'] or ''
                    email = contact['email'] or ''
                except Exception as e:
                    wechat = ''
                    phone = ''
                    resume = ''
                    email = ''
                    logger.info(f'exception_filter:{candidate_id}, {candidate_name}, {c[6]}, {contact}, {e}, {e.args}, {traceback.format_exc()}')
            try:
                conversation = json.loads(c[7])
                con_str = ''
                for c in conversation:
                    con_str = con_str + c['speaker'] + ':' + c['msg'] + '\n'
            except Exception as e:
                con_str = ''

            if len(candidate_info) == 0:
                logger.info(f"chat_candidate_not_match, {candidate_id}")
                region = ''
                position = ''
                edu = ''
                work = ''
                language = ''
            else:
                c_j = candidate_info[0][7].replace('\n','.')
                c_j = c_j.replace("\'", '\"')
                candidate_json = json.loads(c_j, strict=False)
                region = candidate_json.get('profile', {}).get('location', '')
                position = candidate_json.get('profile', {}).get('role', '')
                edu = ''
                for s in candidate_json.get('profile', {}).get('educations', []):
                    edu = edu + s.get('schoolName', '') + ',' + s.get('majorInfo', '') + ',' + s.get('degreeInfo', '') + '\n' + s.get('timeInfo', '') + '\n' + s.get('summary', '') + '\n\n'
                work = ''
                for e in candidate_json.get('profile', {}).get('experiences', []):
                    work = work + e.get('companyName', '') + ',' + e.get('timeInfo', '') + '\n'
                    for wo in e.get('works', []):
                        work = work + "positon:" + wo.get('workPosition', '') + '\n'
                        work = work + "time:" + wo.get('workTimeInfo', '') + '\n'
                        work = work + "location:" + wo.get('workLocationInfo', '') + '\n'
                        work = work + "description:" + wo.get('workDescription', '') + '\n\n'
                language = ''
                for lan in candidate_json.get('profile', {}).get('languages', []):
                    language = language + lan.get('language', '') + '\n' + lan.get('des', '') + '\n\n'

            l = [job_id, candidate_id, create_time, candidate_name, source, wechat, phone, email, resume, con_str, region, position, edu, work, language]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'test_download_candidate_linkedin_error4, {c_j}')
            logger.info(f'test_download_candidate_linkedin_error4,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

def generate_candidate_csv_by_job_maimai(job_id, start_date, end_date):
    chat_list = get_chats_by_job_id_with_date(job_id, start_date, end_date)
    job_name = get_job_name_by_id(job_id)
    io = StringIO()
    w = csv.writer(io)

    l = ['岗位名称','候选人ID', '创建时间', '候选人姓名','来源','微信','电话','简历','对话详情','地区','性别','年龄', '岗位', '最高学历', '专业', '历史公司', '毕业院校', '教育经历', '工作经历', '预期地点', '预期薪水', '简历标签']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for c in chat_list:
        try:
            candidate_info = query_candidate_by_id(c[2])
            job_name = job_name
            candidate_id = c[2]
            create_time = c[9].strftime("%Y-%m-%d %H:%M:%S")
            candidate_name = c[3]
            if c[4] == 'user_ask':
                source = '候选人主动'
            elif c[4] == 'search':
                source= '机器人打招呼'
            else:
                source = '未知'
            if c[6] is None :
                wechat = ''
                phone = ''
                resume = ''
            else:
                try:
                    contact = json.loads(c[6])
                    wechat = contact['wechat'] or ''
                    phone = contact['phone'] or ''
                    resume = contact['cv'] or ''
                except Exception as e:
                    wechat = ''
                    phone = ''
                    resume = ''
                    logger.info(f'exception_filter:{candidate_id}, {candidate_name}, {c[6]}, {contact}, {e}, {e.args}, {traceback.format_exc()}')
            try:
                conversation = json.loads(c[7])
                con_str = ''
                for c in conversation:
                    con_str = con_str + c['speaker'] + ':' + c['msg'] + '\n'
            except Exception as e:
                con_str = ''


            if len(candidate_info) == 0:
                logger.info(f"chat_candidate_not_match, {candidate_id}")
                region = ''
                gender = ''
                age = 0
                position = ''
                degree = ''
                major = ''
                large_comps = ''
                school = ''
                edu = ''
                work = ''
                exp_location = ''
                exp_salary = ''
                tag_list = ''
            else:
                c_j = candidate_info[0][7].replace('\n','.')
                c_j = c_j.replace("\'", '\"')
                candidate_json = json.loads(c_j, strict=False)
                region = candidate_info[0][4]
                if candidate_json.get('gender', 0) == 0:
                    gender = '未知'
                elif candidate_json.get('gender', 0) == 1:
                    gender = '男'
                elif candidate_json.get('gender', 0) == 2:
                    gender = '女'
                else:
                    gender = '未知'
                age = candidate_json.get('age', -1)
                position = candidate_info[0][5]
                if candidate_json.get('degree', -1) == 0:
                    degree = '大专'
                elif candidate_json.get('degree', -1) == 1:
                    degree = '本科'
                elif candidate_json.get('degree', -1) == 2:
                    degree = '硕士'
                elif candidate_json.get('degree', -1) == 3:
                    degree = '博士'
                else:
                    degree = '未知'
                major = candidate_json.get('major', '')
                large_comps = ','.join(candidate_json.get('companies', []))
                school = ''
                if len(candidate_json.get('education', [])) > 0:
                    school = candidate_json['education'][0].get('school', '')
                edu = ''
                for s in candidate_json.get('education', []):
                    edu = edu + s.get('school', '') + ',' + s.get('department', '') + ',' + s.get('sdegree', '') + ',' + s.get('v', '') + '\n'
                work = ''
                for e in candidate_json.get('work', []):
                    des = e.get('description', '') or ''
                    work = work +','+ e.get('company', '') + ',' + e.get('position', '') + ',' + e.get('worktime', '') + ',' + e.get('v', '') + ',' + des + '\n'
                exp_location = candidate_json.get('exp_location', '')
                exp_salary = candidate_json.get('exp_salary', '')
                tag_list = ','.join(candidate_json.get('tag_list', []))

            l = [job_id, candidate_id, create_time, candidate_name, source, wechat, phone, resume, con_str, region, gender, age, position, degree, major, large_comps, school, edu, work, exp_location, exp_salary, tag_list]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'test_download_candidate_maimai_error4, {c_j}')
            logger.info(f'test_download_candidate_maimai_error4,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

def pNull(s):
    if s is None or s == None or s =='null':
        return ''
    return s or ''

def generate_resume_csv_Linkedin(manage_account_id, platform, start_date, end_date, list_name):
    res = get_resume_by_filter(manage_account_id, platform, start_date, end_date, list_name)
    io = StringIO()
    w = csv.writer(io)

    l = ['候选人ID', '创建时间', '候选人姓名', '电话', '邮箱', '地区', '岗位', '最高学历', '专业', '毕业院校','年龄', '教育经历', '工作经历', '语言能力', '工作总结']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for r in res:
        try:
            candidate_id = r[1]
            create_time = r[4].strftime("%Y-%m-%d %H:%M:%S")
            profile_json = r[5].replace('\n', ',')
            profile_json = profile_json.replace('/', '_')
            profile_json = profile_json.replace('，', ',')
            profile_json = profile_json.replace('u0000', ',')
            profile_json = profile_json.replace('\\', ',')
            profile = json.loads(profile_json, strict=False).get('profile', {})
            candidate_name = profile.get('name', '')
            phone = ','.join(profile.get('phones', []))
            email = ','.join(profile.get('emails', []))
            region = profile.get('location', '')
            position = profile.get('role', '')
            sdegree = ''
            if len(profile.get('educations', [])) > 0:
                sdegree = profile.get('educations', [])[0].get('degreeInfo', '')
            major = ''
            if len(profile.get('educations', [])) > 0:
                major = profile.get('educations', [])[0].get('majorInfo', '')
            school = ''
            if len(profile.get('educations', [])) > 0:
                school = profile.get('educations', [])[0].get('schoolName', '')
            age = -1
            for i in range(len(profile.get('educations', []))-1, -1, -1):
                time_info = profile.get('educations', [])[i].get('timeInfo', '')
                if time_info != '':
                    index = -1
                    for idx, ch in enumerate(time_info):
                        if ch.isdigit():
                            index = idx
                            break
                    if index != -1:
                        age = int(datetime.datetime.today().year) - int(time_info[index: index + 4]) + 18
                        break

            edu = ''
            for e in profile.get('educations', []):
                edu = f"{edu}{pNull(e.get('schoolName', ''))},{pNull(e.get('majorInfo', ''))},{pNull(e.get('degreeInfo', ''))},{pNull(e.get('timeInfo', ''))},{pNull(e.get('summary', ''))}\n"
            work = ''
            for e in profile.get('experiences', []):
                work = f"{work}{pNull(e.get('companyName', ''))},{pNull(e.get('timeInfo', ''))}\n"
                for wo in e.get('works', []):
                    work = f"{work}{pNull(wo.get('workTimeInfo', ''))},{pNull(wo.get('worklocationInfo', ''))},{pNull(wo.get('workPosition', ''))},{pNull(wo.get('workDescription', ''))}\n"
                
            languages = ''
            for lan in profile.get('languages', []):
                languages = f"{languages}{pNull(lan.get('language', ''))},{pNull(lan.get('des', ''))}\n"
            summary = profile.get('summary', '')
            
            l = [candidate_id, create_time, candidate_name,phone, email, region, position, sdegree, major, school, age, edu, work, languages, summary]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'download_resume_error_linkedin,{profile_json}')
            logger.info(f'download_resume_error_linkedin,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')


def generate_resume_csv_maimai(manage_account_id, platform, start_date, end_date):
    res = get_resume_by_filter(manage_account_id, platform, start_date, end_date)
    io = StringIO()
    w = csv.writer(io)

    l = ['候选人ID', '创建时间', '候选人姓名','地区','性别', '年龄','工作总时长', '在职公司', '岗位', '最高学历', '专业', '历史公司', '毕业院校', '教育经历', '工作经历', '预期职位', '预期地点', '预期薪水', '其他倾向', '简历标签']
    l_encode = [csv_encode(_l) for _l in l]
    l_encode[0] = codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+l_encode[0]
    w.writerow(l_encode)
    yield io.getvalue()
    io.seek(0)
    io.truncate(0)
    for r in res:
        try:
            candidate_id = r[1]
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
            gender = profile.get('gender_str', '')
            age = profile.get('age', 0)
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
            l = [candidate_id, create_time, candidate_name, region,gender, age, work_time, company, position, sdegree, major, large_comps, school, schools, work_detail, exp_positon, exp_location, exp_salary, exp_prefer, tags]
            l_encode = [csv_encode(_l) for _l in l]
            w.writerow(l_encode)
            yield io.getvalue()
            io.seek(0)
            io.truncate(0)
        except Exception as e:
            logger.info(f'download_resume_error4,{profile_json}')
            logger.info(f'download_resume_error4,{candidate_id}, {e}, {e.args}, {traceback.format_exc()}')

def format_json_str(body):
    r = ""
    if type(body) == list:
        for sub in body:
            r += format_json_str(sub)
            r += "\n"
    elif type(body) == dict:
        for k in body:
            r += k
            r += ":"
            r += format_json_str(body[k])
            r += '\t'
    elif type(body) == str:
        r = body[1:-1] if len(body) > 0 and body[0] == "\"" and body[-1] == "\"" else body
    return r

def fetch_json_str(body, key, default_v = ''):
    return format_json_str(body[key ]) if key in body else default_v

def generate_csv(res):
    s = res[0][6].replace('\n', '\\n')
    res_l = json.loads(s)
    format_resume_json = json.loads(res[0][8].replace('\n', '\\n'))
    io = StringIO()
    w = csv.writer(io)
    w.writerow(['简历', '结果', '匹配结果', '姓名', '性别', '年龄/出生', '期望职位', '期望薪资', '最高学历', '专业', '工作经历', '教育经历', '工作城市', '电话', '邮箱', '技能', '项目经历'])
    for idx, r in enumerate(res_l):
        file_name = os.path.basename(r['f_path'])
        l = [file_name, r['res'], r['remark'],
            fetch_json_str(format_resume_json[idx], '姓名'), fetch_json_str(format_resume_json[idx], '性别'),
            fetch_json_str(format_resume_json[idx], '年龄/出生'), fetch_json_str(format_resume_json[idx], '期望职位'),
            fetch_json_str(format_resume_json[idx], '期望薪资'), fetch_json_str(format_resume_json[idx], '最高学历'),
            fetch_json_str(format_resume_json[idx], '专业'), fetch_json_str(format_resume_json[idx], '工作经历'),
            fetch_json_str(format_resume_json[idx], '教育经历'), fetch_json_str(format_resume_json[idx], '工作城市'),
            fetch_json_str(format_resume_json[idx], '电话'), fetch_json_str(format_resume_json[idx], '邮箱'),
            fetch_json_str(format_resume_json[idx], '技能'), fetch_json_str(format_resume_json[idx], '项目经历')]
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

def download_file(url):
    file_name = os.path.basename(url)
    responsepdf = requests.get(url)
    if responsepdf.status_code == 200:
        dst_path = os.path.join(file_path_prefix, file_name)
        with open(dst_path, "wb") as f:
            f.write(responsepdf.content)
        return dst_path
    else:
        return None

def content_transfer(f_path):
    file_name = os.path.basename(f_path)
    if f_path.endswith('jpg') or f_path.endswith('jpeg') or f_path.endswith('png'):
        return True, img_to_text(f_path)
    elif f_path.endswith('pdf'):
        final_url_list = []
        start_time = datetime.datetime.now()
        pdf = fitz.open(f_path)
        for page in pdf:
            mat=fitz.Matrix(10,10)
            pix = page.get_pixmap(matrix=mat)
            png_file_name = f"{file_name.split('.')[0]}-page-{page.number}.png"
            pix.save(png_file_name)
            final_url_list.append(png_file_name)
        pdf.close()
        end_pdf_time = datetime.datetime.now()
        res = imglist_to_text(final_url_list)
        end_txt_time = datetime.datetime.now()
        logger.info(f'[tool_service] content transfer pdf -> jpg time consumption = {(end_pdf_time - start_time).total_seconds()}, jpg -> text time consumption = {(end_txt_time - end_pdf_time).total_seconds()}')
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
    start_time = datetime.datetime.now()
    ext_prompt_msg = '以下是候选人信息，请提取关键信息并结构化输出\n$$$\n' + file_raw_data[0:3500] + "\n$$$"
    ext_prompt = Prompt()
    ext_prompt.add_user_message(ext_prompt_msg)
    file_key_data = gpt_manager.chat_task(ext_prompt)
    end_format_time = datetime.datetime.now()
    # file_key_data = chatgpt.chat(ext_prompt)
    extract_prompt_msg = '你是一个猎头, 请从候选人信息提取: 姓名, 性别, 年龄/出生, 期望职位, 期望薪资, 最高学历, 专业, 教育经历, 工作经历, 工作城市, 电话, 邮箱, 技能, 项目经历.\n如果候选人信息不包含该字段, 标记为空, 请用中文回答, 以json格式输出'
    extract_prompt_msg += f'$$$\n候选人个人信息如下：{file_key_data}\n$$$\n'
    extract_prompt = Prompt()
    extract_prompt.add_user_message(extract_prompt_msg)
    extract_info = gpt_manager.chat_task(extract_prompt)
    format_info = {}
    try:
        if '```json' in extract_info:
            extract_info = extract_info.replace('```json', '')
        if '```' in extract_info:
            extract_info = extract_info.replace('```', '')
        format_info = json5.loads(extract_info)
    except BaseException:
        pass
    end_parse_time = datetime.datetime.now()
    logger.info(f"filter_task_content_extract_and_filter_file_key_data: {file_key_data}")
    prefix = '你是一个猎头，请判断候选人是否符合招聘要求\n给出具体原因和推理过程\n答案必须在最后一行，并且单独一行 A.合适，B.不合适'
    candidate_msg = f'$$$\n候选人个人信息如下：{file_key_data}\n$$$\n'
    filter_prompt_msg = prefix + candidate_msg + '\n招聘要求:\n' + jd + '\n'
    filter_prompt = Prompt()
    filter_prompt.add_user_message(filter_prompt_msg)
    res = gpt_manager.chat_task(filter_prompt)
    end_judge_time = datetime.datetime.now()

    logger.info(f'[content_extract_and_filter] format resume time = {(end_format_time - start_time).total_seconds()}, parse result time = {(end_parse_time - end_format_time).total_seconds()}, judge time = {(end_judge_time - end_parse_time).total_seconds()}')
    # res = chatgpt.chat(filter_prompt)
    return res, format_info

def exec_filter_task(manage_account_id, file_list, jd):
    filter_result = []
    format_resume_infos = []
    for f_path in file_list:
        flag, file_raw_data = content_transfer(f_path)
        logger.info(f"filter_task_content_transfer:{f_path}, {flag}, {len(file_raw_data)}, {file_raw_data[0:3500]}")
        file_name = basename(f_path)
        if not flag:
            logger.info(f'file_ext_not_support, {manage_account_id}, {f_path}')
            filter_result.append({
                "f_path": file_name,
                "res": file_raw_data,
                "remark":""
            })
            continue

        single_filter_result, format_resume_info = content_extract_and_filter(file_raw_data, jd)
        logger.info(f"filter_task_content_extract_and_filter:{f_path}, {single_filter_result}, {format_resume_info}")
        res = 'QUALIFIED' if 'A.合适' in single_filter_result else 'UNQUALIFIED'
        filter_result.append({
            "f_path": file_name,
            "res": res,
            "remark": single_filter_result
        })
        format_resume_infos.append(format_resume_info)
    return filter_result, format_resume_infos


def deserialize_raw_profile(raw_profile):
    if raw_profile is None or (type(raw_profile) == tuple and len(raw_profile) == 0):
        return None
    while (type(raw_profile) == tuple):
        raw_profile = raw_profile[0]
    if type(raw_profile) == str:
        return json.loads(raw_profile)
    return None

def get_leave_msg(candidate_id, platform):
    raw_profile = get_raw_latest_profile_by_candidate_id_and_platform(candidate_id, platform)
    raw_profile = deserialize_raw_profile(raw_profile)
    if not raw_profile:
        logger.info('[tools_service] without raw profile for candidate_id = {}, platform = {}'.format(candidate_id, platform))
        return None, 'no candidate'
    name = None
    if 'profile' in raw_profile and 'name' in raw_profile['profile']:
            name = raw_profile['profile']['name']

    location = None
    if 'profile' in raw_profile and 'location' in raw_profile['profile']:
            location = raw_profile['profile']['location']

    role = 'candidate'
    if 'profile' in raw_profile and 'role' in raw_profile['profile']:
            role = raw_profile['profile']['role']

    company_name = None
    if 'profile' in raw_profile and 'experiences' in raw_profile['profile'] and len(raw_profile['profile']['experiences']) > 0 and 'companyName' in raw_profile['profile']['experiences'][0]:
        company_name = raw_profile['profile']['experiences'][0]['companyName']

    msg = 'Hi '+ name + ' , ' if name else'Hi ,'
    msg += 'we are looking for an ' + role + ' base in Irvine/Seattle for FFALCON who is expanding streaming business, it\'s the leading smart TVs & AIoT company in China, '
    if company_name:
        msg += 'your Exp. in ' + company_name + ' seems a good match, '
    msg += 'would you like to explore this opportunity? Thanks!'
    return msg, None

def apply_chat_scenario(candidate_id, platform):
    scenario_options = ['要简历', '约电话', '转介绍', '召回']
    raw_profile = get_raw_latest_profile_by_candidate_id_and_platform(candidate_id, platform)
    logger.info('[apply_chat_scenario] raw_profile = {}'.format(raw_profile))
    raw_profile = deserialize_raw_profile(raw_profile)
    name = None
    if raw_profile and 'profile' in raw_profile and 'name' in raw_profile['profile']:
            name = raw_profile['profile']['name']
    ret = {}
    for scenario in scenario_options:
        msg = 'Hi ' + name + ' ,\n' if name else 'Hi, \n'
        if scenario == '要简历':
            msg += 'Thanks for getting back to me! Could you please send me your updated resume so we can move forward to the next step? Also, can I have your availability for a short call to discuss this opportunity further.\nLooking forward to hearing from you soon. Thanks!'
        if scenario == '约电话':
            msg += 'Thanks for the updated resume and I\'ve well received! Meanwhile, can I have your availability for a short call to discuss this opportunity further.\nLooking forward to hearing from you soon. Thanks!'
        if scenario == '转介绍':
            msg += 'Thanks for the reply, I understand you\'re not actively looking for a new job right now. However, I\'d greatly appreciate your insights. Do you happen to know someone in your network who might be interested in this role? Feel free to pass along the details, and if they have questions, they can reach out directly.\nThanks again for any help you can provide!'
        if scenario == '召回':
            msg += 'Thanks for connecting! I trust this message finds you in good spirits. I noticed your noteworthy background on LinkedIn!\nCurrently, FFALCON is on a global expansion drive. It\'s the sub-brand of TCL Electronics, an established global TV manufacturing brand. To strengthen TCL Corporation’s globalization strategy plans within the smart home sector, FFalcon has been developed into a leading brand with a business value of over 650 million USD.\nI believe your insights could significantly contribute to our strategy, and I would like to discuss more details about this opportunity with you! Would you mind sharing a concise update on your CV? Your expertise aligns with our objectives, and your input would be immensely valuable.'
        ret[scenario] = [msg]
    return ret, None

_tag_id_cache = {}
_tag_name_id_cache = {}

def ensure_cache(manage_account_id, platform):
    if manage_account_id not in _tag_id_cache:
        _tag_id_cache[manage_account_id] = {}
        _tag_name_id_cache[manage_account_id] = {}
        id_tags = query_profile_id_tag(manage_account_id, platform)
        for id_tag in id_tags:
            _tag_id_cache[manage_account_id][id_tag[0]] = id_tag[1]
            _tag_name_id_cache[manage_account_id][id_tag[1]] = id_tag[0]
    return _tag_id_cache[manage_account_id], _tag_name_id_cache[manage_account_id]

def get_check_tag_ids(manage_account_id, tags, platform):
    user_id_tag_cache, user_tag_id_cache = ensure_cache(manage_account_id, platform)
    tag_ids = []
    for tag in tags:
        if tag not in user_tag_id_cache:
            return None
        else:
            tag_ids.append(user_tag_id_cache[tag])
    return tag_ids

def create_profile_tag(manage_account_id, platform, tag):
    try:
        tag_id = create_profile_tag_db(manage_account_id, platform, tag)
    except BaseException as e:
        logger.error("[tool_service] create profile tag failed for {}, {}, {}".format(manage_account_id, platform, tag))
        return None, "创建profile tag失败"
    user_id_tag_cache, user_tag_id_cache = ensure_cache(manage_account_id, platform)
    user_id_tag_cache[tag_id] = tag
    user_tag_id_cache[tag] = tag_id

    return {'tag_id': tag_id, 'tag': tag, 'manage_account_id': manage_account_id, 'platform': platform, 'tag': tag}, None

def query_profile_tag_by_user(manage_account_id, platform):
    user_id_tag_cache, user_tag_id_cache = ensure_cache(manage_account_id, platform)
    tags = list(user_tag_id_cache.keys())
    return tags, None

def query_profile_tag_relation_by_user_and_candidate(manage_account_id, candidate_id, platform):
    id_tags = query_profile_tag_relation_by_user_and_candidate_db(manage_account_id, candidate_id, platform)
    tags = []
    for id_tag in id_tags:
        tags.append(id_tag[1])

    return tags, None

def associate_profile_tags(manage_account_id, candidate_id, platform, tags):
    tag_ids = get_check_tag_ids(manage_account_id, tags, platform)
    if not tag_ids:
        return None, "tags中存在无效tag"
    for idx, tag_id in enumerate(tag_ids):
        relations = query_id_by_profile_tag_relation(manage_account_id, candidate_id, platform, [tags[idx]])
        if relations and len(relations) > 0:
            logger.info("[tool_service] associate_profile_tag existing relation manage_account_id = {}, candidate_id = {}, platform = {}, tag_id = {}, tag = {}", manage_account_id, candidate_id, platform, tag_id, tags[idx])
            continue
        associate_profile_tag(manage_account_id, candidate_id, platform, tag_id, tags[idx])
        logger.info("[tool_service] associate_profile_tag manage_account_id = {}, candidate_id = {}, platform = {}, tag_id = {}, tag = {}", manage_account_id, candidate_id, platform, tag_id, tags[idx])
    return tags, None

def deassociate_profile_tags(manage_account_id, candidate_id, platform, tags):
    tag_ids = get_check_tag_ids(manage_account_id, tags, platform)
    if not tag_ids:
        return None, "tags中存在无效tag"
    delete_profile_tag_relation(manage_account_id, candidate_id, platform, tags)
    logger.info("[tool_service] delete_profile_tag_relation manage_account_id = {}, candidate_id = {}, platform = {}, tag_ids = {}, tags = {}", manage_account_id, candidate_id, platform, tag_ids, tags)
    return tags, None

def delete_profile_tags(manage_account_id, candidate_id, platform, tags):
    user_id_tag_cache, user_tag_id_cache = ensure_cache(manage_account_id, platform)
    tag_ids = get_check_tag_ids(manage_account_id, tags, platform)
    if not tag_ids:
        return None, "tags中存在无效tag"
    relations = query_id_by_profile_tag_relation(manage_account_id, candidate_id, platform, tags)
    if relations and len(relations) != 0:
        return None, "存在标记的tag关系, 请先清除profile和tag关系"
    delete_profile_tags_db(tag_ids)
    for idx, tag in enumerate(tags):
        user_id_tag_cache.pop(tag_ids[idx])
        user_tag_id_cache.pop(tag)
    logger.info("[tool_service] delete manage_account_id = {}, candidate_id = {}, platform = {}, tags = {}", manage_account_id, candidate_id, platform, tags)
    return None, None

def transfer_profile():
    # to do refactor for download excel
    return None

def search_profile_by_tag(manage_account_id, platform, tags, page, limit):
    tag_ids = get_check_tag_ids(manage_account_id, tags, platform)
    if not tag_ids:
        return None, "tags中存在无效tag"
    candidate_ids = query_candidate_id_by_tag_relation(manage_account_id, platform, tags)
    total_count = get_resume_total_count_by_candidate_ids_and_platform(manage_account_id, platform, candidate_ids)
    start = (page - 1)*limit
    rows = get_resume_by_candidate_ids_and_platform(manage_account_id, platform, candidate_ids, start, limit)
    details = []
    data = {'page': page, 'limit':limit, 'total': total_count, 'details': details}

    for row in rows:
        detail = {'candidateId' : row[0], 'department': None, 'title': None, 'name':None, 'location':None, 'contactInfo': None, 'cv':None, 'cvUrl': row[2]}
        details.append(detail)
        raw_profile = row[1]
        raw_profile = deserialize_raw_profile(raw_profile)
        if not raw_profile:
            continue
        if 'profile' in raw_profile and 'name' in raw_profile['profile']:
            detail['name'] = raw_profile['profile']['name']

        location = None
        if 'profile' in raw_profile and 'location' in raw_profile['profile']:
            detail['location'] = raw_profile['profile']['location']

        if 'profile' in raw_profile and 'contactInfo' in raw_profile['profile']:
            detail['contactInfo'] = raw_profile['profile']['contactInfo']

        if 'profile' in raw_profile and 'role' in raw_profile['profile']:
            detail['title'] = raw_profile['profile']['role']

    return data, None



