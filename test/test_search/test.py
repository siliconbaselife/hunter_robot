from service.llm_agent_service import *

query = "宁德时代在美国的对标公司?"
print(f"问题: {query}")
docs = google_search(5, query)
print(f"搜索结果: {docs}")
agent = searchAgent()
r = agent.cal(query, docs)
print(f"结果: {r}")
