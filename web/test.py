def _parse_contact(msg):
        filter_msg = msg
        parse_dict = {}
        wx_start = -1
        find = False
        for idx, c in enumerate(msg):
            istarget =  (c >='a' and c<='z') or (c>='A' and c<='Z') or (c>='0' and c<='9') or c=='-' or c=='_'
            # print(f'id {idx}-----{c}------{istarget}')
            if istarget:
                if wx_start<0:
                    wx_start = idx
            else:
                if wx_start>-1:
                    range_len = idx - wx_start
                    if range_len>=6 and range_len<=20:
                        find = True
                        parse_dict['contact'] = msg[wx_start:idx]
                        filter_msg = ''
                        break
                wx_start = -1
        if not find and wx_start >-1:
            range_len = len(msg)- wx_start
            if range_len>=6 and range_len<=20:
                parse_dict['contact'] = msg[wx_start:idx]
                filter_msg = ''
        # logger.info(f'maimai chat log: msg filter input {msg} out {filter_msg}')
        return filter_msg, parse_dict



# if __name__ == "__main__":
#     from dao.task_dao import *
#     judge_result = {
#         'judge': True,
#         'details': '12312321\n213213'
#     }
#     filter_result = json.dumps(judge_result, ensure_ascii=False)
#     candidate_id = '111'
#     job_id = 'jjj'
#     prompt = 'sdfsdf'
#     insert_filter_cache(candidate_id, job_id, prompt, filter_result)



if __name__ == "__main__":
    detail =  {
        "id": 233025019,
        "name": "杨得草",
        "age": 28,
        "gender": 1,
        "degree": 1,
        "candidate_status": 0,
        "active": "在线",
        "exp_location": "陕西-西安",
        "exp_location_dict": {
            "region": [
                "陕西西安"
            ],
            "cities": [
                "西安"
            ]
        },
        "exp_salary": "15k-20k/月",
        "major": "",
        "exp_position": "高招HR",
        "exp_positon_name": [
            "HR",
            "招聘主管",
            "行政主管"
        ],
        "education": [
            {
                "school": "西安建筑科技大学",
                "sdegree": "本科",
                "start_date_ym": "2014-01",
                "end_date_ym": "2018-01",
                "department": "汉语言文学"
            }
        ],
        "work": [
            {
                "company": "成都卓唯企业管理咨询有限公司",
                "timeinfo": "2021-03至2023-03",
                "locationInfo": "",
                "position": "猎头顾问",
                "description": "专注于职能类（行政/HR/采购等）岗位，支持互联网/游戏/科技/人工智能等行业；寻猎岗位包括但不限于如下:-行政：综合行政运营/行政经理/总监，行政COE（综合运营/工程/福利/安全/餐饮/活动/数字化）-采购：IT//市场/行政/人力外包/专业服务采购，采购COE-HR:  招聘专家，HRBP/HRD，COE(OTD/LD/C&B/OC)，SSC-PR/GR以上方向职位可Base: 上海/杭州/北京/深圳/广州"
            }
        ],
        "companies": [
            "比亚迪",
            "成都卓唯企业管理咨询有限公司",
            "碧桂园"
        ],
        "tag_list": [
            "SSC",
            "招聘咨询",
            "社会招聘",
            "招聘配置"
        ],
        "active_time": 1699928376,
        "job_preferences": {
            "positions": [
                "HR",
                "招聘主管",
                "行政主管"
            ],
            "regions": [
                "陕西西安"
            ],
            "province_cities": [
                "西安"
            ],
            "salary": "15k-20k/月",
            "prefessions": [
                "猎头行业",
                "游戏行业",
                "视频网站/直播"
            ]
        }
    }
    if detail['gender'] == 0:
        gender = '男'
    else:
        gender = '女'
    if detail['degree'] == 2:
        sdegree = '硕士'
    elif detail['degree'] == 3:
        sdegree = '博士'
    elif detail['degree'] == 1:
        sdegree = '本科'
    else:
        sdegree = '未知'

    edu = ''
    for e in detail['education']:
        edu = edu + '学校:' + e['school'] + ',学位:' + e['sdegree'] + ',' + e['start_date_ym'] + '至' + e['end_date_ym'] + ',专业:' + e['department'] + '\n'

    work = ''
    for w in detail['work']:
        work = work + '公司:' + w['company'] + ',在职时间:' + w['timeinfo'] + ',工作地点相关:' + w['locationInfo'] + ',工作岗位:' + w['position'] + ',工作描述:' + w['description'] + '\n'

    prompt = f'候选人个人信息如下：\n姓名:{detail["name"]}\n性别:{gender} \n期望职位:{detail["exp_positon_name"]}\n年龄：{detail["age"]}\n最高学历:{sdegree}\n学校经历:\n{edu}工作经历:\n{work}'
    

    edu_dict = []
    for e in detail['education']:
        edu_dict.append({
            "学校": e['school'],
            "学位": e['sdegree'],
            "开始时间":e['start_date_ym'],
            "结束时间":e['end_date_ym'],
            "专业":e['department']
        }) 
    work_dict = []
    for w in detail['work']:
        work_dict.append({
            "公司":w['company'],
            "在职时间":w['timeinfo'],
            "工作地点":w['locationInfo'],
            "工作岗位":w['position'],
            "工作描述":w['description']
        })


    p_json = {
        "姓名":detail["name"],
        "性别":gender,
        "期望职位":detail["exp_positon_name"],
        "年龄":detail["age"],
        "最高学历":sdegree,
        "工作经历":work_dict,
        "学校经历":edu_dict
    }

    prompt = f'$$$\n候选人个人信息如下：{p_json}\n$$$\n'



    print(prompt)
