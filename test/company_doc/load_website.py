from langchain_community.document_loaders import WebBaseLoader
from tool_dao import update_company_website_info
from dao.tool_dao import query_company_infos
from dao.tool_dao import update_company_website_info
import json


def run():
    company_infos = query_company_infos()
    for company_info in company_infos:
        company_id = company_info["company_id"]
        print(company_id)
        linkedin_doc = company_info["linkedin_doc"]
        linkedin_info = json.loads(linkedin_doc)
        website = linkedin_info["website"]
        try:
            loader = WebBaseLoader(link)
            docs = loader.load()
        except BaseException as e:
            print(f"googleSearchAgent 链接 {link} 获取不到内容")
        doc = str(docs[0].page_content)
        doc = doc.replace("\n", " ")
        update_company_website_info(company_id, doc)


if __name__ == "__main__":
    print("load website begin")
    run()

    print("load website end")
