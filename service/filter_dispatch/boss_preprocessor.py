
def boss_preprocess(raw_candidate_info):
    tmp = raw_candidate_info
    geek_card = tmp['geekCard']
    edu_experience = tmp['showEdus']
    work_experience= tmp['showWorks']

    ## parse base info\
    cid, cname, age_desc, degree = geek_card['geekId'], geek_card['geekName'], \
                                                geek_card['ageDesc'], geek_card['geekDegree']
    age = int(age_desc[:-1])
    active = tmp['activeTimeDesc']

    ## parse expect
    exp_location = geek_card['expectLocationName']
    exp_salary = geek_card['salary']
    position_name = geek_card['expectPositionName']

    ## parse edu info
    education = []
    for item in edu_experience:
        if item['degreeName']== degree:
            education.append({
                'school': item['school'],
                'major': item['major'],
            })
            break

    ## parse 
    work = []
    for item in work_experience:
        work.append({
            'company': item['company'],
            'position': item['positionName'],
            'responsibility': item['responsibility'],
            'emphasis': ','.join(item['workEmphasisList']) if item['workEmphasisList'] is not None else '',
            'start': item['startDate'],
            'end': item['endDate']
        })

    return {
        'id': cid,
        'name': cname,
        'age': age,
        'degree': degree,
        'active': active,
        'exp_location': exp_location,
        'exp_salary': exp_salary,
        'exp_position': position_name,
        'education': education,
        'work': work
    }