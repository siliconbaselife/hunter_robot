import requests


def test_chat():
    params = {
        'user_id': 'lishundong2009@163.com',
        'account_id': 'test',
        'candidate_id': 'www.linkedin.com/in/myoungkyou-ha-9ba40511a',
        'details': [
            {"speaker": "robot",
             "msg": "Hi, Louisa Keddad, I am recruiting for Anxin Web Shield, and we are currently hiring IT engineers in Algeria. Your background seems well-suited for this position. Would you be interested in discussing it further?,Location: Algiers",
             "time": 1711937400},
            {"speaker": "user", "msg": "yes, please", "time": 1711957400}
        ]
    }

    r = requests.post('http://www.shadowhiring.cn/backend/chat/chat', json=params)
    print(f"confs: {r.text}")


if __name__ == "__main__":
    print("开始测试linkedin chat api接口")
    test_chat()
    print("测试完毕")
