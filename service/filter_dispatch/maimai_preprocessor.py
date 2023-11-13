from .utils import ensure_valid
import json
import traceback
from utils.log import get_logger
from utils.config import config
import time
logger = get_logger(config['log']['log_file'])




def maimai_preprocess(raw_candidate_info):
    try:
        tmp = raw_candidate_info
        cid = tmp['id']
        cname = tmp['name']
        #1男，2女
        gender = tmp['gender']
        #1本科2硕士3博士
        degree = tmp['degree']
        #0貌似是在职，不过感觉并不准确
        candidate_status = tmp["candidate_status"]
        #文字描述感觉意义不大
        active = tmp['active_state']
        
        if 'province' not in tmp or tmp['province'] is None:
            tmp['province'] = ""
        if 'city' not in tmp or tmp['city'] is None:
            tmp['city'] = ""
        if 'major' not in tmp or tmp['major'] is None:
            tmp['major'] = ""
        if 'position' not in tmp or tmp['position'] is None:
            tmp['position'] = ""
        if 'job_preferences' not in tmp or tmp['job_preferences'] is None:
            tmp['job_preferences'] = []


        cur_location = tmp['province'] + '-' + tmp['city']
        
        exp_location = {
            "region": tmp['job_preferences']['regions'],
            "cities": tmp['job_preferences']['province_cities']
        }

        exp_salary = tmp['job_preferences']['salary']
        
        #类似运营/编辑
        major = tmp.get('major', "")
        #类似直播电商风控
        position_name = tmp.get('position', "")
        exp_positon_name = tmp['job_preferences']['positions']
        
        #工作年头
        work_time = 0 if '年' not in tmp.get('work_time', "") else int(tmp.get('work_time',"0").split('年')[0])

         #     [
            #   {
            #     "sid": 33,
            #     "school": "东南大学",
            #     "v": "2013-09至2015-06",
            #     "description": "",
            #     "department": "国际商务",
            #     "sdegree": "硕士",
            #     "degree": 2,
            #     "judge": 0,
            #     "start_date": "2013-09-01",
            #     "start_date_ym": "2013-09",
            #     "end_date_ym": "2015-06",
            #     "school_url": "https://i9.taou.com/maimai/p/school/small_20088e8e9e4c1f275c8e9024bbbc29fc.jpg"
            #   }
        # ]
        education = []
        for e in tmp.get('edu', []):
            education.append({
                'school': e.get('school', ''),
                'sdegree': e.get('sdegree', ''),
                'start_date_ym': e.get('start_date_ym', ''),
                'end_date_ym': e.get('end_date_ym', ''),
                'department': e.get('department', '')
            })
        #  "companies": [
        #     "宝时得科技（中国）有限公司",
        #     "美的集团",
        #     "同程旅行"
        #     ]
        companies = tmp.get('companies', [])
        # [
        #     {
        #         "cid": 874305,
        #         "company": "宝时得科技（中国）有限公司",
        #         "v": "2019-01至2020-11",
        #         "description": "跨境电商运营",
        #         "position": "跨境电商运营",
        #         "worktime": "1年10个月",
        #         "start_date": "2019-01-01",
        #         "judge": 0,
        #         "is_leave": 1,
        #         "start_date_ym": "2019-01",
        #         "end_date_ym": "2020-11",
        #         "company_info": {
        #         "name": "宝时得科技（中国）有限公司",
        #         "cid": 874305,
        #         "clogo": "https://i9.taou.com/maimai/c/offlogo/8ddabb1c0dde47149665c90b6530838a.jpeg",
        #         "share_url": "https://maimai.cn/company?webcid=xkvLzdC8"
        #         }
        # }]
        work = []
        for w in tmp.get('exp'):
            work.append({
                'company': w.get('company', ''),
                'timeinfo': w.get('v', ''),
                'locationInfo': '',
                'position': w.get('position', ''),
                'description': w.get('description', ''),
            })
        
        #不知道怎么来的，反正算一些tag
        tag_list = tmp['tag_list']

        age = 0
        ##parse age
        if tmp['degree'] == 1:
            age = work_time + 23
        elif tmp['degree'] == 2:
            age = work_time + 25
        elif tmp['degree'] == 3:
            age = work_time + 28
        
        active_time = int(time.time()) - int(tmp['second'])

        # {
        #     "positions": [
        #         "游戏主策划",
        #         "主数值"
        #     ],
        #     "regions": [
        #         "上海"
        #     ],
        #     "province_cities": [
        #         "上海"
        #     ],
        #     "salary": "50k-70k/月",
        #     "prefessions": []
        #     }
        
        job_preferences = tmp['job_preferences']

        return {
            'id': cid,
            'name': cname,
            'age': age,
            'gender': gender,
            'degree': degree,
            'candidate_status': candidate_status,
            'active': active,
            'exp_location': cur_location,
            'exp_location_dict': exp_location,
            'exp_salary': exp_salary,
            'major': major,
            'exp_position': position_name,
            'exp_positon_name': exp_positon_name,
            'education': education,
            'work': work,
            'companies': companies,
            'tag_list': tag_list,
            "active_time": active_time,
            "job_preferences":job_preferences
        } 

    except BaseException as e:
        logger.info(f'candidate filter preprocess fail  {cid}, {cname} failed for {e}, {traceback.format_exc()}')
        with open(f'test/fail/{cid}_{cname}.json', 'w') as f:
            f.write(json.dumps(raw_candidate_info, indent=2, ensure_ascii=False))
        return {
            'id': cid,
            'name': cname,
            'age': age,
            'gender': gender,
            'degree': degree,
            'candidate_status': candidate_status,
            'active': active,
            'exp_location': cur_location,
            'exp_location_dict': exp_location,
            'exp_salary': exp_salary,
            'major': major,
            'exp_position': position_name,
            'exp_positon_name': exp_positon_name,
            'education': education,
            'work': work,
            'companies': companies,
            'tag_list': tag_list,
            "active_time": active_time,
            "job_preferences":job_preferences
        } 




    