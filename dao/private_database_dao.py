from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger

logger = get_logger(config['log']['log_file'])

table_names = {}


def query_private_tags(tag):
    select_columns = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_names[tag]}'"
    raw_columns = dbm.query(select_columns)
    columns = []
    for column in raw_columns:
        if column == 'id':
            continue

        if column == 'profile':
            continue

        columns.append(column)

    tag_infos = {}
    for column in columns:
        sql = f"select distinct('{column}') from '{table_names[tag]}'"
        rows = dbm.query(sql)
        tag_infos[column] = []
        for row in rows:
            tag_infos[column].append(row)

    return tag_infos

def
