import requests
import json

data = {
    'accountID': 'account_test',
    'candidateID': 'candidate_test',
    'jobID': 'job_test',
    'candidateName': 'candidate test',
    'historyMsg': [
        {"speaker": "robot", "msg": "我这里有个国电通的岗位，考虑下不呢?"},
        {"speaker": "user", "msg": "你好"}
    ]
}

r = requests.post('http://127.0.0.1:2040/recruit/candidate/chat', json=data)
print(json.loads(r.text, strict=False))
