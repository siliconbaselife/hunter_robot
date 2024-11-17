from langchain_community.document_loaders import WebBaseLoader
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

website = "https://www.solarlandscape.com/"
try:
    loader = WebBaseLoader(website)
    loader.requests_kwargs = {'verify': False, "timeout": 10}
    docs = loader.load()
except BaseException as e:
    print(f"googleSearchAgent 链接 {website} 获取不到内容")

print(docs)