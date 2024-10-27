from service.llm_agent_service import *

query = "印尼劳动法规定年假一年多少天?"

google_key_agent = googleKeyAgent()
key_words = google_key_agent.cal(query)
print(f"key_words => {key_words}")

google_search_agent = googleSearchAgent()
comprehend_agent = comprehendAgent()

relation_txts = []
for key_word in key_words:
    print(f"key_word => {key_word}")
    relation_txt = google_search_agent.cal(key_word, query)
    relation_txts.extend(relation_txt)

res = comprehend_agent.cal(relation_txts, query)

print("-----------------")
print(f"问题: {query}")
print(f"生成keywords: {key_words}")
print(f"google搜索到相关文章 {len(relation_txts)} 条")
print(f"最终AI答案: {res}")
