import mysql.connector
from mysql.connector import errorcode

from logger import get_logger
from config import config
from threading import RLock, current_thread

logger = get_logger(config['log_file'])

def init_db_conn():
    cnx = None
    try:
        cnx = mysql.connector.connect(
            host=config['db']['host'],
            port=config['db']['port'],
            db=config['db']['name'],
            user=config['db']['user'],
            passwd=config['db']['pwd'],
            autocommit=True
        )
        if cnx.is_connected():
            logger.info('db connection init done')
        else:
            logger.info('db connection init failed')
            cnx = None
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.info('Something is wrong with your user name or password')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.info('Database does not exist')
        else:
            logger.info(err)
    if not cnx.is_connected():
        return None
    return cnx


def ensure_conn(cnx):
    if not cnx.is_connected():
        cnx.reconnect(attempts=3, delay=1)


def exec_sql(cnx, sql, insert=False, error_msg=None, try_cnt=3):
    print(f'sql: {sql}')
    ensure_conn(cnx)
    while True:
        try:
            cursor = cnx.cursor()
            cursor.execute(sql)
            logger.info(sql)
            if insert:
                return cursor.lastrowid
            else:
                return cursor.fetchall()
        except BaseException as ex:
            exp = ex
            try_cnt -= 1
            if try_cnt == 0:
                if error_msg is not None:
                    logger.error('[db] exec sql = {} failed error msg = {}'.format(sql, error_msg))
                else:
                    logger.error('[db] exec sql = {} failed'.format(sql))
                logger.exception(exp)
                break
    return None


# # todo orm refactor
# def query_apps(cnx):
#     query_sql = 'SELECT * FROM apps'
#     return exec_sql(cnx, query_sql)


# def update_app_tokens(cnx, app_id, tokens):
#     update_sql = 'UPDATE apps set chatgpt_tokens = {} where id = {}'.format(tokens, app_id)
#     exec_sql(cnx, update_sql)


# def log_user(cnx, app_id, user_obj):
#     sql = 'INSERT INTO wechat_users (app_id, wechat_user_id, chatgpt_tokens) values (\'{}\',\'{}\', \'0\')  \
#            ON DUPLICATE KEY UPDATE \
#            update_time = values(update_time), chatgpt_tokens = values(chatgpt_tokens)'.format(app_id, user_obj.wechat_user_id)
#     return exec_sql(cnx, sql, insert=True)


# def query_user(cnx, wechat_user_id):
#     query_sql = 'SELECT * FROM wechat_users \
#          where wechat_user_id = \'{}\' '.format(wechat_user_id)
#     return exec_sql(cnx, query_sql)


# def increase_user_tokens(cnx, wechat_user_id, tokens):
#     sql = 'UPDATE wechat_users SET chatgpt_tokens = chatgpt_tokens + \'{}\' where wechat_user_id = \'{}\''.format(
#         tokens,
#         wechat_user_id)
#     return exec_sql(cnx, sql)


# def query_topic_by_id(cnx, db_id):
#     query_sql = 'SELECT * FROM chat_topic WHERE app_id = \'{}\''.format(db_id)
#     return exec_sql(cnx, query_sql)


# def increase_topic_tokens(cnx, topic, tokens):
#     sql = 'UPDATE chat_topic SET chatgpt_tokens = chatgpt_tokens + \'{}\' WHERE topic = \'{}\''.format(tokens, topic)
#     return exec_sql(cnx, sql)


# def query_chat_black_list_words(cnx):
#     query_sql = 'SELECT * FROM chat_black_list_word'
#     return exec_sql(cnx, query_sql)


# def query_prompt_by_topic(cnx, topic):
#     query_sql = 'SELECT initial_prompt FROM chat_topic where topic = \'{}\''.format(topic)
#     r = exec_sql(cnx, query_sql)
#     if r is not None:
#         return r[0]
#     else:
#         return None

def new_job(cnx, job_name, job_jd, robot_api):
    sql = "INSERT INTO `job` (job_name, job_jd, robot_api)" \
          "VALUES('{}', '{}', '{}') ".format(job_name, job_jd, robot_api)
    return exec_sql(cnx, sql, insert=True)


def new_user(cnx, job_name, boss_id):
    sql = "INSERT INTO `user` (job_name, boss_id)" \
          "VALUES('{}', '{}') ".format(job_name, boss_id)
    return exec_sql(cnx, sql, insert=True)

def query_robotapi(cnx, boss_id):
    sql = "SELECT job.robot_api from job, user where user.boss_id='{}' and job.job_name=user.job_name ".format(boss_id)
    r = exec_sql(cnx, sql)
    if r is None or len(r)==0:
        return None
    else:
        return r[0][0]

def new_candidate(cnx, boss_id, candidate_id, candidate_name=None, status='init', details=None):
    sql = "INSERT INTO `candidate` (boss_id, candidate_id, candidate_name, status, details)" \
          "VALUES('{}', '{}', '{}', '{}', '{}') ".format(
        boss_id, candidate_id, candidate_name, status, details)
    return exec_sql(cnx, sql, insert=True)

def update_candidate(cnx, boss_id, candidate_id, status, details):
    sql = "UPDATE candidate SET status = '{}', details='{}' WHERE boss_id = '{}' AND candidate_id='{}' ".format(
        status, details, boss_id, candidate_id
    )
    return exec_sql(cnx, sql)

def query_candidate(cnx, boss_id, candidate_id):
    sql = "SELECT status, details FROM candidate WHERE boss_id = '{}' AND candidate_id='{}' ".format(
        boss_id, candidate_id
    )
    r = exec_sql(cnx, sql)
    if r is None or len(r)==0:
        return None
    else:
        r = r[0]
        return r[0], r[1]

thread_db_conn = {}
db_rlock = RLock()
service_container = {}


def get_db_conn():
    global thread_db_conn
    with db_rlock:
        thread_id = current_thread().ident
        if thread_id not in thread_db_conn:
            thread_db_conn[thread_id] = init_db_conn()
        return thread_db_conn[thread_id]
