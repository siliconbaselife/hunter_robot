import requests


def get_conf():
    params = {
        "user_id": "lishundong2009@163.com"
    }
    r = requests.post('http://www.shadowhiring.cn/backend/chat/get_conf', json=params)
    print(f"confs: {r.text}")


def add_conf():
    params = {
        "user_id": "lishundong2009@163.com",
        "tag": "test",
        "content": {
            "positive": "positive",
            "negtive": "negtive",
            "recall": "recall"
        }
    }
    r = requests.post('http://www.shadowhiring.cn/backend/chat/conf', json=params)
    print(f"confs: {r.text}")


if __name__ == "__main__":
    print("开始测试conf api接口")
    get_conf()
    add_conf()
    get_conf()
    print("测试完毕")
