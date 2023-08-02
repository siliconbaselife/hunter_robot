
def boss_preprocess(raw_candidate_info):
    tmp = raw_candidate_info['zpData']['geekDetailInfo']
    base_info = tmp['geekBaseInfo']
    edu_experience = tmp['geekEduExpList']
    work_experience= tmp['geekWorkExpList']
    show_position = tmp['showExpectPosition']

    ## parse base info
    cid, cname, age, degree, active, time_to_work = base_info['userId'], base_info['name'], base_info['ageDesc'], base_info['degreeCategory'], \
                                                        base_info['activeTimeDesc'], base_info['applyStatusDesc']
    age = int(age[:-1])

    ## parse expect
    exp_location = show_position['locationName']
    exp_salary = show_position['salaryDesc']
    position_name = show_position['positionName']

    ## parse edu info
    education = []
    for item in edu_experience:
        if item['degreeName']== degree:
            education.append({
                'school': item['school'],
                'major': item['major'],
                'tags': item['tags']
            })
            break

    ## parse 
    work = []
    for item in work_experience:
        work.append({
            'company': item['company'],
            'position': item['positionName'],
            'responsibility': item['responsibility'],
            'emphasis': item['workEmphasis'],
            'department': item['department'],
            'start': item['startYearMonStr'],
            'end': item['endYearMonStr']
        })

    return {
        'id': cid,
        'name': cname,
        'age': age,
        'degree': degree,
        'active': active,
        'time_to_work': time_to_work,
        'exp_location': exp_location,
        'exp_salary': exp_salary,
        'exp_position': position_name,
        'education': education,
        'work': work
    }