import requests
data = {
    'accountID': 'linkedin1',
    'candidateID': 'candidate1',
    'jobID': 'test1',
    'candidateName': 'candidate test',
    'historyMsg': [{"speaker": "robot", "msg": "hi"}, {"speaker": "user", "msg": "hi"}]
}

requests.post('http://127.0.0.1:2040/recruit/candidate/chat', json=data)

