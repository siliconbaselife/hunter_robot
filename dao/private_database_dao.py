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
        tag_infos[column] = {}
        sql_type = f"DESCRIBE '{table_names[tag]}' `tag_type`"
        rows = dbm.query(sql_type)
        column_type = rows[0][1]
        if column_type == 'int':
            tag_infos[column]["column_type"] = "number"
        else:
            tag_infos[column]["column_type"] = "varchar(255)"
            sql = f"select distinct('{column}') from '{table_names[tag]}'"
            rows = dbm.query(sql)
            tag_infos[column]["enumeration"] = []
            for row in rows:
                tag_infos[column]["enumeration"].append(row)

    return tag_infos


def query_private_tag_filter_num(tag, column_infos):
    table_name = table_names[tag]
    sql = f'select count(*) from {table_name}'
    if len(column_infos) > 0:
        sql += ' where '

    for i, column in enumerate(column_infos.keys()):
        column_content = column_infos[column]
        type = column_content["column_type"]
        value = column_content["value"]
        if type == "number":
            sql += f" {column} BETWEEN {value[0]} and {value[1]} "
        else:
            sql += f" {column} == {value}"

        if i < len(column_infos.keys()) - 1:
            sql += "and"

    rows = dbm.query(sql)

    return rows[0][0]


def query_private_tag_filter_profiles(tag, column_infos):
    table_name = table_names[tag]
    sql = f'select profile from {table_name}'
    if len(column_infos) > 0:
        sql += ' where '

    for i, column in enumerate(column_infos.keys()):
        column_content = column_infos[column]
        type = column_content["column_type"]
        value = column_content["value"]
        if type == "number":
            sql += f" {column} BETWEEN {value[0]} and {value[1]} "
        else:
            sql += f" {column} == {value}"

        if i < len(column_infos.keys()) - 1:
            sql += "and"

    rows = dbm.query(sql)

    return rows
