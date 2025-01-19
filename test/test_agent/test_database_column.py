from dao.private_database_dao import query_private_tags

if __name__ == "__main__":
    r = query_private_tags('lishundong2009@163.com', 'huawei')
    print(r)
