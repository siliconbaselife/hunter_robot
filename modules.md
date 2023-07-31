# modules

## web

## db utils
#### 设计表结构:
```
job
account
task
candidate
```
#### 接口
```
new_job
query_job_id

new_account
query_account_id

query_robotapi
new_candidate
query_candidate
update_candidate
```

## chat
#### 功能
> 聊天会话管理

#### 接口
```
```

## task manager
#### 功能
> 管理不同账户的任务，接收账户的任务完成反馈，每天根据原始任务和已完成的任务排列剩余任务
#### 接口
```
# 初始化某个账户的任务
init_task
# 获取一个账户当天的任务（可能会多次调用）
fetch_task(account_id)
# 账户完成情况更新
update_task(account_id, details)
```

## candidate strategy
#### 功能
> 候选人筛选策略，根据不同岗位的需求对候选人条件进行筛选
#### 接口
```
filter_candidate(job_id, candidate_info)
```