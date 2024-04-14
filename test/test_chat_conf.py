import requests


def get_conf():
    params = {
        "user_id": "lishundong2009@163.com"
    }
    r = requests.post('http://127.0.0.1:13333/backend/chat/get_conf', json=params)
    print(f"confs: {r.text}")


if __name__ == "__main__":
    print("开始测试conf api接口")
    print("测试完毕")
