import requests
import json

data = {
    "accountID": "account_test",
    "candidateIDs": ["candidate_test"],
    "candidateIDs_read": ["candidate_test"]
}

r = requests.post('http://127.0.0.1:2040/recruit/candidate/recallList', json=data)
print(json.loads(r.text, strict=False))
