from dao.tool_dao import *
from utils.db_manager import dbm
from service.tools_service import parse_profile

step = 1000
id_start = 1
id_end = id_start + step


while True:
    rows = dbm.query('select id, profile from online_resume where id >= {} and id <= {}'.format(id_start, id_start))
    print('query {} row of {} - {}'.format(len(rows), id_start, id_end))

    for row in rows:
        rid = row[0]
        p = row[1]
        profile = parse_profile(p, '')


