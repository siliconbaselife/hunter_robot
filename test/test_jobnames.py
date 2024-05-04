import requests


def test_query():
    params = {
        'manage_account_id': "lishundong2009@163.com",
        'account_id': "account_Boss_111735749"
    }

    r = requests.post('http://www.shadowhiring.cn/account/jobnames/fetch', json=params)
    print(f"confs: {r.text}")


def test_set():
    params = {
        'manage_account_id': "lishundong2009@163.com",
        'account_id': "account_Boss_111735749",
        'jobnames': ["测试1", "测试2"]
    }

    r = requests.post('http://www.shadowhiring.cn/account/jobnames/set', json=params)
    print(f"confs: {r.text}")


if __name__ == "__main__":
    test_query()
    test_set()
    test_query()
