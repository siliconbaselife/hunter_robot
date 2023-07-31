

import pymysql
from threading import Lock


class DBManager:
    def __init__(self, host, port, user, password, database, charset):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None
        self.cursor = None
        self.lock = Lock()
        self.init_db()

    def init_db(self):
        self.connection = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                          database=self.database, charset=self.charset, autocommit=True)
        self.cursor = self.connection.cursor()

    def reconnect(self):
        try:
            self.connection.ping()
        except BaseException as e:
            self.connection()

    def close_db(self):
        self.lock.acquire()
        self.cursor.close()
        self.connection.close()
        self.lock.release()

    def query(self, sql):
        self.lock.acquire()
        self.reconnect()
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        self.lock.release()
        return data

    def update(self, sql):
        self.lock.acquire()
        self.reconnect()
        self.cursor.execute(sql)
        self.connection.commit()
        self.lock.release()

    def alter(self, sql):
        self.lock.acquire()
        self.reconnect()
        self.cursor.execute(sql)
        self.connection.commit()
        self.lock.release()

    def delete(self, sql):
        self.lock.acquire()
        self.reconnect()
        self.cursor.execute(sql)
        self.connection.commit()
        self.lock.release()

    def insert(self, sql, data):
        self.lock.acquire()
        self.reconnect()
        self.cursor.executemany(sql, data)
        self.connection.commit()
        self.lock.release()

    def drop_table(self, sql):
        self.lock.acquire()
        self.reconnect()
        self.cursor.execute(sql)
        self.connection.commit()
        self.lock.release()

    def exist_table(self, table_name):
        self.lock.acquire()
        self.reconnect()
        exist = self.cursor.execute("show tables like '%s'" % table_name)
        self.connection.commit()
        self.lock.release()
        return exist


host = '127.0.0.1'
port = 3306
user = 'wordpress'
password = 'wordpress'
database = 'aistormy'
charset = 'utf8'


# host = '10.253.209.26'
# port = 33006
# user = 'beta'
# password = 'kVkBhpSVa6!3'
# database = 'fangdao_image_server'
# charset = 'utf8'

dbm = DBManager(host=host, port=port, user=user, password=password, database=database, charset=charset)
