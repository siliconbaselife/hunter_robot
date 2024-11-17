from langchain_community.document_loaders import WebBaseLoader

website = "http://www.solarturbines.com"
try:
    loader = WebBaseLoader(website)
    docs = loader.load()
except BaseException as e:
    print(f"googleSearchAgent 链接 {website} 获取不到内容")

print(docs)