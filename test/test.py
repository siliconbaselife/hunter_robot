import requests
import json

data = {
    'accountID': 'account_test',
    'candidateID': 'candidate_test',
    'jobID': 'job_test',
    'candidateName': 'candidate test',
    'historyMsg': [
        {"speaker": "robot", "msg": "hi"},
        {"speaker": "user", "msg": "hi"}
    ]
}

r = requests.post('http://127.0.0.1:20400/recruit/candidate/chat', json=data)
print(json.loads(r.text, strict=False))
