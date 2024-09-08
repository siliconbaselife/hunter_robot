from service.llm_agent_service import ChatAgent

chat_agent = ChatAgent()
res = chat_agent.chat("", [], "hi")
print(f"res => {res}")