from utils.db_manager import dbm
from utils.config import config
from utils.log import get_logger
from utils.utils import deal_json_invaild
import json
import traceback

logger = get_logger(config['log']['log_file'])


def is_huawei_exist(candidate_id):
    sql = f"select count(1) from huawei where candidate_id = '{candidate_id}'"
    row = dbm.query(sql)
    return row[0][0] == 1


def add_profile(profile_info):
    candidate_id = profile_info['candidate_id']
    age = profile_info['age']
    name = profile_info['name']
    company = profile_info['company']
    chinese = profile_info['chinese']
    graduate_school = profile_info['graduate_school']
    education_background = profile_info['education_background']
    school_level = profile_info['school_level']
    five_years_jump_times = profile_info['five_years_jump_times']
    service_or_product_type = profile_info["service_or_product_type"]
    function_type = profile_info["function_type"]
    service_country = profile_info["service_country"]
    rank_of_position = profile_info["rank_of_position"]
    department = profile_info["department"]
    cooperative_department = profile_info["cooperative_department"]

    insert = f"insert into huawei(candidate_id, Age, Name, Company, Chinese, Graduate_School, Education_Background, School_Level, Five_Years_Jump_Times, " \
             f"Service_Or_Product_Type, Function_type, Service_Country, Rank_Of_Position, Department, Cooperative_Department) " \
             f"values('{candidate_id}', '{age}', '{name}', '{company}', '{chinese}', '{graduate_school}', '{education_background}', '{school_level}', '{five_years_jump_times}', " \
    f"'{service_or_product_type}', '{function_type}', '{service_country}', '{rank_of_position}', '{department}', '{cooperative_department}')"

    print(insert)
    dbm.insert(insert)
