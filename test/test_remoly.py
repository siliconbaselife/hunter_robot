import requests
import json

data = {
    "accountID": "",
    "candidateIDs": [],
    "candidateIDs_read": []
}

r = requests.post('http://127.0.0.1:20400/recruit/candidate/recallList', json=data)
print(json.loads(r.text, strict=False))