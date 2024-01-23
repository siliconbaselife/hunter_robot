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

def linkedin_online_resume_upload_processor(manage_account_id, profile, platform):
    count = 0
    for p in profile:
        candidate_id = get_candidate_id(p, platform)
        if candidate_id == None or candidate_id == '':
            continue
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
                schoolName = edu.get('schoolName', '') or ''
                edu['schoolName'] = schoolName.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            summary = p.get('profile', {}).get('summary', '') or ''
            role = p.get('profile', {}).get('role', '') or ''
            location = p.get('profile', {}).get('location', '') or ''
            name = p.get('profile', {}).get('name', '') or ''
            contact_info = json.dumps(p.get('profile', {}).get('contactInfo', {}), ensure_ascii=False)
            p['profile']['contactInfo'] = contact_info.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['summary'] = summary.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['role'] = role.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['location'] = location.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            p['profile']['name'] = name.replace('"', "").replace("'", "").replace("\n", ";").replace('\"', "").replace("\'", "")
            upload_online_profile(manage_account_id, platform, json.dumps(p, ensure_ascii=False), candidate_id)
            count = count + 1
    return count

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

    l = ['岗位名称','候选人ID', '创建时间', '候选人姓名','来源','微信','电话','简历','对话详情','地区','岗位', '学校经历', '公司经历', '语言能力']
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

            l = [job_id, candidate_id, create_time, candidate_name, source, wechat, phone, resume, con_str, region, position, edu, work, language]
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

def generate_resume_csv_Linkedin(manage_account_id, platform, start_date, end_date):
    res = get_resume_by_filter(manage_account_id, platform, start_date, end_date)
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
    if key not in body:
        return default_v
    format_json_str(body[key])

    return json.dumps(body[key], ensure_ascii=False) if key in body else default_v

def generate_csv(res):
    s = res[0][6].replace('\n', '\\n')
    res_l = json.loads(s)
    format_resume_json = json.loads(res[0][8].replace('\n', '\\n'))
    io = StringIO()
    w = csv.writer(io)
    w.writerow(['简历', '结果', '匹配结果', '姓名', '性别', '年龄/出生', '期望职位', '期望薪资', '最高学历', '专业', '教育经历', '工作经历', '工作城市', '电话', '邮箱', '技能', '项目经历'])
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

    logger.info(f"filter_task_content_extract_and_filter_file_key_data: {file_key_data}")
    prefix = '你是一个猎头，请判断候选人是否符合招聘要求\n给出具体原因和推理过程\n答案必须在最后一行，并且单独一行 A.合适，B.不合适'
    candidate_msg = f'$$$\n候选人个人信息如下：{file_key_data}\n$$$\n'
    filter_prompt_msg = prefix + candidate_msg + '\n招聘要求:\n' + jd + '\n'
    filter_prompt = Prompt()
    filter_prompt.add_user_message(filter_prompt_msg)
    res = gpt_manager.chat_task(filter_prompt)
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

