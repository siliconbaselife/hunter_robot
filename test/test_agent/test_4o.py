from service.llm_agent_service import CompanyAgent


agent = CompanyAgent()
r = agent.chat('sales', '英国', '家庭储能')
print(r)