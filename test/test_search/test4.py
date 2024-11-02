from service.business_service import agent_chat_search_service
import time

begin = time.time()
res, _ = agent_chat_search_service("lishundong2009@163.com", "remoly是一家做什么的公司")
end = time.time()

print(f"结果 => {res}")
print(f"耗时 => {end - begin}")

