from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger

logger = get_logger(config['log']['log_file'])

table_names = {
    "lishundong2009@163.com": {
        "华为": "huawei"
    }
}


def query_private_tags_old(manage_account_id, tag):
    table = table_names[manage_account_id][tag]

    select_columns = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
    raw_columns = dbm.query(select_columns)
    columns = []
    for column in raw_columns:
        if column == 'id':
            continue

        if column == 'profile':
            continue

        if column == 'create_time':
            continue

        if column == 'update_time':
            continue

        columns.append(column)

    tag_infos = {}
    for column in columns:
        tag_infos[column] = {}
        sql_type = f"DESCRIBE '{table}' `tag_type`"
        rows = dbm.query(sql_type)
        column_type = rows[0][1]
        if column_type == 'int':
            tag_infos[column]["column_type"] = "number"
        else:
            tag_infos[column]["column_type"] = "varchar(255)"
            sql = f"select distinct('{column}') from '{table}'"
            rows = dbm.query(sql)
            tag_infos[column]["enumeration"] = []
            for row in rows:
                tag_infos[column]["enumeration"].append(row[0])

    return tag_infos


def query_private_tags(manage_account_id, tag):
    table = table_names[manage_account_id][tag]
    sql = f"show columns from {table}"
    print(sql)
    rows = dbm.query(sql)
    print(rows)

    tag_infos = {}
    for row in rows:
        column = row[0]
        column_type = row[1]

        if column == 'id' or column == 'profile' or column == 'create_time' or column == 'update_time' or column == 'candidate_id':
            continue

        if column == 'Name':
            tag_infos[column]["column_type"] = "string"

        if column_type == 'int':
            tag_infos[column]["column_type"] = "number"
        else:
            tag_infos[column]["column_type"] = "string"
            sql = f"select distinct('{column}') from '{table}'"
            rows = dbm.query(sql)
            tag_infos[column]["enumeration"] = []
            for row in rows:
                tag_infos[column]["enumeration"].append(row[0])

    return tag_infos


def query_private_tag_filter_num(manage_account_id, tag, column_infos):
    table_name = table_names[manage_account_id][tag]
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


def query_private_tag_filter_profiles(manage_account_id, tag, column_infos, page, limit):
    table_name = table_names[manage_account_id][tag]
    sql = f'select candidate_id, profile from {table_name}'
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

    sql += f" limit {page}, {limit}"

    rows = dbm.query(sql)

    return rows
