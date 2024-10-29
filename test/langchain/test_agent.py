from service.llm_agent_service import ChatAgent

chat_agent = ChatAgent()
res = chat_agent.chat("", [], "想了解下菲律宾劳动法")
print(f"res => {res}")