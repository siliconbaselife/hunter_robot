# hunter_robot

## interface API

### 接口说明：
```
调用方式:            POST
request params:     json的方式放在body里面
request file:       上传文件
返回的统一格式:      {'data':xxx, 'ret': 0}
response data:      指的是上述的data字段，默认json方式
```

#### 注册job
```
## uri: /recruit/job/register
## request params:
### platformType    string      need      平台类型，如：boss
### platformID      string      need      平台上job的id
### jobName         string      need      工作名称
### jobJD           string      need      工作介绍
### robotApi        string      need      岗位对应的算法后端api
## response data:
### jobID           string      工作ID
```

#### 查询jobID
```
## uri: /recruit/job/query
## request params:
### platformType    string      need      平台类型，如：boss
### platformID      string      need      平台上job的id
## response data:
### jobID           string      工作ID
```

#### 注册账户（招聘账户，账户的岗位信息在平台上面自行配置）
```
## uri: /recruit/account/register
## request params:
### platformType    string      need      招聘平台，例如：'boss' 
### platformID      string      need      招聘平台给的账户ID，例如：'27175761'
### jobs            list        need      账户招聘的岗位jobID列表
## response data:
### accountID       string      账户ID
```

#### 查询账户ID
```
## uri: /recruit/account/query
## request params:
### platformType    string      need      招聘平台，例如：'boss' 
### platformID      string      need      招聘平台给的账户ID，例如：'27175761'
## response data:
### accountID       string      账户ID
```

#### 获取账户任务(当天)
```
## uri: /recruit/account/task/fetch
## request params:
### accountID       string      need      账户ID
## response data:
### task            list        当天任务(要给所有job都执行任务)，例如：
[
  {
    "helloSum": 50,
    "taskType": "batchTouch",
    "timeMount": [
      {
        "time": "09:00",
        "mount": 25
      },
      {
        "time": "16:00",
        "mount": 25
      }
    ]
  }
]
```

#### 上报账户任务执行情况
```
## uri: /recruit/account/task/report
## request params:
### accountID       string      need        账户ID
### taskStatus      list        need        任务完成情况，例如：
[
  {
    "taskType": "batchTouch",
    "details": {
      "candidateList": ["123445", "333442"]  ##这里就是打过招呼的候选人的candidateID列表 
    }
  }
]
## response data:
### status          string        ok        
```

#### 判断是否打招呼
```
## uri: /recruit/candidate/filter
## request params:
### accountID       string      need        账户ID
### jobID           string      deprecated  要招聘的岗位ID。当前版本不再传这个字段，默认使用account注册的第一个job
### candidateID     string      need        候选人在招聘平台上的id，比如boss上的geekid，如果别的平台没有这个标识，可以用类似{name}_{age}_{education}的方法代替
### candidateInfo   dict        need        候选人详情，例如，boss平台候选人页面的json信息
## response data:
### touch           bool        true        
```

#### 对话
```
## uri: /recruit/candidate/chat
## request params:
### accountID       string      need        账户ID
### jobID           string      deprecated  要招聘的岗位ID。当前版本不再传这个字段，默认使用account注册的第一个job
### candidateID     string      need        候选人在招聘平台上的id，比如boss上的geekid，如果别的平台没有这个标识，可以用类似{name}_{age}_{education}的方法代替
### candidateName   string      need        候选人姓名
### historyMsg      list        need        候选人详情，例如：
[
  {
    "speaker": "robot",
    "msg": "您好"
  },
  {
    "speaker": "user",
    "msg": "还招人么"
  },
  {
    "speaker": "system",
    "msg": "候选人同意给微信"
  }
]
## response data:
### nextStep        string      下一步动作，例如：
normal_chat,finish,algo_abnormal,need_ensure
### nextStepContent string      给候选人的回复消息
```

#### 上报联系人的结果（联系方式）
```
## uri: /recruit/candidate/result
## request params:
### accountID       string      need        账户ID
### jobID           string      need        要招聘的岗位ID
### jobID           string      deprecated  要招聘的岗位ID。当前版本不再传这个字段，默认使用account注册的第一个job{name}_{age}_{education}的方法代替
### candidateName   string      need        候选人姓名
### phone           string      option      候选人手机号
### wechat          string      option      候选人微信号
## request file:
### cv              file            option      候选人简历
## response data:
### status          string        ok        
```


### 二次召回话术接口
```
## uri:   /recruit/candidate/recallList
## request params:
### accountID       string      need        账户ID
### candidateIDs    list      need        候选人id
[
  "id1", "id2", "id3"
]
## response data:
{'ret': 0, 'msg': 'success', 'data': data}
##data
[
  {
    "candidate_id":"id1",
    "need_recall": True,
    "recall_msg":"看您有心理咨询证书，和我们岗位要求非常匹配，请问您是否方便交换个联系方式或简历呢？"
  }
]

```

### 二次召回话术接口
```
## uri:   /recruit/candidate/recallResult
## request params:
### accountID       string      need        账户ID
### candidateID    string      need        候选人id

## response data:
{'ret': 0, 'msg': 'success', 'data': data}


```

### 微信相关接口
# 具体任务
/wechat/candidate/taskToDo
request param
string account_id

response
task_list
[{
  "task_type":"send_msg",
  "content":[{
    "alias_id":"1111",
    "msg":"dfdfdfdfd"
  }]
},
{
  "task_type":"add_friend",
  "content":[
    {
      "search_id":"id1",
      "alias_id":"xxxx"
    }
  ]
}
]

# 上报消息发送
/wechat/candidate/msgSendReport
request 
string account_id
string alias_id
string msg_send

# 上报添加用户
/wechat/candidate/addFriendReport
request
string account_id
string search_id
string alias_id

# 上报用户新消息
/wechat/candidate/userMsguser
request
string account_id
string alias_id
string msg_receive

response
{'ret': 0, 'msg': 'success', 'data': {"msg":"xxxxxxxxx"}}


