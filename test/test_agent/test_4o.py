from service.llm_agent_service import CompanyAgent
from service.llm_agent_service import JDAgent

# agent = CompanyAgent()
# r = agent.chat('sales', '英国', '家庭储能')

jd_agent = JDAgent()
r = jd_agent.chat('sales', '储能', '伦敦', 'lishundong1991@163.com', '')
print(r)