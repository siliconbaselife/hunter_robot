from dao.tool_dao import *
from utils.db_manager import dbm
from service.tools_service import deserialize_raw_profile



def get_company(profile):
    experience = profile['experiences'][0] if 'experiences' in profile and len(profile['experiences']) > 0 else None
    if experience and 'companyName' in experience:
        company = experience['companyName']
    elif 'company' in profile:
        company = profile['company']
    else:
        company = ''

    if company is None:
        company = ''
    return company.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')

def main():
    step = 1000
    id_start = 100001
    id_end = id_start + step
    count = 0
    while True:
        query_sql = 'select id, raw_profile from online_resume where id >= {} and id <= {}'.format(id_start, id_end)
        print(query_sql)
        rows = dbm.query(query_sql)
        print('query {} row of {} - {}, updated = {}'.format(len(rows), id_start, id_end, count))
        if len(rows) == 0:
            print('done')
            break

        for row in rows:
            rid = row[0]
            p = row[1]
            profile = deserialize_raw_profile(p)
            if profile is None:
                continue
            if 'profile' in profile:
                profile = profile['profile']
            name = profile['name'] if 'name' in profile else ''
            name = name.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')
            company = get_company(profile)
            sql = f'update online_resume set name = \'{name}\', company = \'{company}\' where id = {rid}'
            # print(f'{sql}')
            dbm.update(sql)
            count += 1

        id_start += step
        id_end += step


def debug():

    id_debug = 33084
    query_sql = 'select id, raw_profile from online_resume where id >= {} and id <= {}'.format(id_debug, id_debug)
    print(query_sql)
    rows = dbm.query(query_sql)
    row  = rows[0]
    rid = row[0]
    p = row[1]
    profile = deserialize_raw_profile(p)
    if 'profile' in profile:
        profile = profile['profile']
    name = profile['name'] if 'name' in profile else ''
    company = profile['company'] if 'company' in profile else ''
    name = name.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')
    company = company.replace("\n", "\\n").replace("\'", "\\'").replace('\"', '\\"')
    sql = f'update online_resume set name = \'{name}\', company = \'{company}\' where id = {rid}'
    print(sql)

if __name__ == '__main__':
    main()
