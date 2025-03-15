from service.llm_agent_service import CompanyAgent
from service.llm_agent_service import JDAgent

agent = CompanyAgent()
# r = agent.chat({"job_position": 'sales', "country": '英国', "industry_type": '储能'})

# jd_agent = JDAgent()
# r = jd_agent.chat(
#     {"job_title": 'sales', "industry": '储能', "location": '伦敦', "application_email": 'lishundong1991@163.com',
#      "additional_requirements": ''})
print(agent.get_prompt({"job_position": 'sales', "country": '英国', "industry_type": '储能'}))
