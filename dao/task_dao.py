from utils.db_manager import dbm

sql_dict = {
    "add_task_count":"update account_exec_log set hello_sum_exec = hello_sum_exec+1 where account_id={} and job_id={} and exec_date={}",
    "get_task":"select * from account_config where account_id={}",
    "insert_sub_task_log":"insert into account_exec_log(account_id, job_id, exec_date, hello_sum_need) values ({},{},{},{})"
}


def get_task(account_id):
    return dbm.query(sql_dict["get_task"].format(account_id))

def init_task_log(account_id, job_id, exec_date, hello_sum_need):
    d = [[account_id, job_id, exec_date, hello_sum_need]]
    return dbm.insert(sql_dict["insert_sub_task_log"], d)

def hello_exec(account_id, job_id, exec_date):
    return dbm.update(sql_dict["add_task_count"].format(account_id, job_id, exec_date))