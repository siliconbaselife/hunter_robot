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
            "positive": "I am currently helping a client (Apri) to find an HRM talent in Seattle, USA. I will be responsible for SSC establishment and recruitment, employee relations and other modules in the USA. \nIf you are interested, I hope you can get a copy of your updated resume. Let’s discuss your career plans in detail!",
            "negtive": "Thanks for getting back to me!\nIf you don't mind, I'd want to know why this opportunity isn't quite hitting the mark for you. I focus on recruiting for the North American market, and I see potential for us to work together in the future!\nAnd hey, if you happen to know anyone else who might be a good fit for this, I'd really appreciate it if you could pass the word along. Thanks a bunch!",
            "recall": "Hi!{name}\nI hope this message finds you well. I wanted to follow up regarding the opportunity we discussed recently. I understand that things can get busy, but I wanted to check in and see if you had any further thoughts or questions about the position.\nIf you're still interested or if you need more information, please let me know. I'm here to help and happy to provide any additional details you might need."
        }
    }
    r = requests.post('http://www.shadowhiring.cn/backend/chat/conf', json=params)
    print(f"confs: {r.text}")


def add_conf2():
    params = {
        "user_id": "lishundong2009@163.com",
        "tag": "test2",
        "content": {
            "positive": "positive2",
            "negtive": "negtive2",
            "recall": "recall2"
        }
    }
    r = requests.post('http://www.shadowhiring.cn/backend/chat/conf', json=params)
    print(f"confs: {r.text}")


if __name__ == "__main__":
    print("开始测试conf api接口")
    # get_conf()
    add_conf()
    # add_conf2()
    # get_conf()
    print("测试完毕")
