import urllib3
import json
import os
from dao.tool_dao import query_company_infos
from dao.tool_dao import update_company_google_search_info
from langchain_core.tools import Tool
from langchain.utilities import GoogleSearchAPIWrapper
from langchain_community.document_loaders import WebBaseLoader

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.environ["GOOGLE_CSE_ID"] = "a5bb86389c8d54e04"
os.environ["GOOGLE_API_KEY"] = "AIzaSyADsE884QVkWz_Y8X1zJMvGl3lVmJ-IbZc"

search = GoogleSearchAPIWrapper(k=10)


def top10_results(query):
    return search.results(query, 10)


tool = Tool(
    name="Google Search Snippets",
    description="Search Google for recent results.",
    func=top10_results,
)


def is_website(link, website):
    name1 = link.replace("http://", "").replace("https://", "").replace("www.", "").split(".")[0]
    name2 = website.replace("http://", "").replace("https://", "").replace("www.", "").split(".")[0]
    print(f"is_website {link} {name1} {website} {name2}")

    if "linkedin" in link:
        return True

    if "youtube" in link:
        return True

    if name1 != name2:
        return False

    return True


def google_search(company_name, website):
    rs = tool.run(company_name)
    num = 0
    google_docs = []
    for r in rs:
        link = r["link"]
        if is_website(link, website):
            print("链接不需要获取")
            continue

        try:
            loader = WebBaseLoader(link)
            loader.requests_kwargs = {'verify': False, "timeout": 10}
            docs = loader.load()
        except BaseException as e:
            print(f"google_search 链接 {link} 获取不到内容")
            continue

        num += 1
        doc = str(docs[0].page_content)
        doc = doc[:1000]
        doc = doc.replace('\\', ' ')
        doc = doc.replace("\n", " ")
        doc = doc.replace("\'", " ")
        doc = doc.replace("\"", " ")
        google_docs.append(doc)
        if num >= 5:
            break

    return google_docs


def run():
    company_infos = query_company_infos()
    for company_info in company_infos:
        company_id = company_info["company_id"]
        linkedin_doc = company_info["linkedin_doc"]
        linkedin_doc = linkedin_doc[1:]
        linkedin_doc = linkedin_doc[:-1]

        google_search_doc = company_info["google_search_doc"]
        if google_search_doc is not None:
            print("已经有搜索内容")
            continue

        linkedin_info = json.loads(linkedin_doc)
        website = linkedin_info["website"]
        company_name = linkedin_info["name"]
        docs = google_search(company_name, website)
        update_company_google_search_info(company_id, json.dumps(docs))


if __name__ == "__main__":
    print("load website begin")
    run()
    print("load website end")
