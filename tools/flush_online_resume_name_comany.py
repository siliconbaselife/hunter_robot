from dao.tool_dao import *
from utils.db_manager import dbm
from service.tools_service import deserialize_raw_profile

step = 1000
id_start = 1
id_end = id_start + step
count = 0

while True:
    rows = dbm.query('select id, raw_profile from online_resume where id >= {} and id <= {}'.format(id_start, id_start))
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
        name = profile['name'] if 'name' in profile else ''
        company = profile['company'] if 'company' in profile else ''
        sql = f'update online_resume set name = \'{name}\', company = \'{company}\''
        print(f'{sql}')
        dbm.update(sql)
        count += 1

    id_start += step
    id_end += step


