

import pymysql
from threading import Lock
from utils.config import config
from utils.log import  get_logger

logger = get_logger(config['log']['db_log_file'])

class DBManager:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.database = database
        # self.charset = charset
        self.connection = None
        self.cursor = None
        self.lock = Lock()
        self.init_db()

    def init_db(self):
        self.connection = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                          database=self.database,charset='utf8mb4', autocommit=True)
        self.cursor = self.connection.cursor()

    def reconnect(self):
        try:
            self.connection.ping()
        except BaseException as e:
            self.connection()

    def close_db(self):
        with self.lock:
            self.cursor.close()
            self.connection.close()

    def query(self, sql):
        logger.info(f'sql query: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            data = self.cursor.fetchall()
            return data

    def update(self, sql):
        logger.info(f'sql update: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            self.connection.commit()

    def alter(self, sql):
        logger.info(f'sql alter: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            self.connection.commit()

    def delete(self, sql):
        logger.info(f'sql delete: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            self.connection.commit()

    def insert_many(self, sql, data):
        logger.info(f'sql insert: {sql}         {data}')
        with self.lock:
            self.reconnect()
            self.cursor.executemany(sql, data)
            self.connection.commit()

    def insert(self, sql):
        logger.info(f'sql insert: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            self.connection.commit()

    def drop_table(self, sql):
        logger.info(f'sql drop_table: {sql}')
        with self.lock:
            self.reconnect()
            self.cursor.execute(sql)
            self.connection.commit()

    def exist_table(self, table_name):
        logger.info(f'sql exist_table: {table_name}')
        with self.lock:
            self.reconnect()
            exist = self.cursor.execute("show tables like '%s'" % table_name)
            self.connection.commit()
            return exist


dbm = DBManager(host=config['db']['host'], 
                port=config['db']['port'], 
                user=config['db']['user'], 
                password=config['db']['pwd'], 
                database=config['db']['name'])