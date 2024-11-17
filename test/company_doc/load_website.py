from langchain_community.document_loaders import WebBaseLoader
from dao.tool_dao import update_company_website_info
from dao.tool_dao import query_company_infos
from dao.tool_dao import update_company_website_info
import json


def run():
    company_infos = query_company_infos()
    for company_info in company_infos:
        company_id = company_info["company_id"]
        print(f"company_id: {company_id}")
        linkedin_doc = company_info["linkedin_doc"]
        linkedin_doc = linkedin_doc[1:]
        linkedin_doc = linkedin_doc[:-1]
        linkedin_info = json.loads(linkedin_doc)
        website = linkedin_info["website"]
        print(f"website: {website}")
        try:
            loader = WebBaseLoader(website)
            loader.requests_kwargs = {'verify': False, "timeout": 5}
            docs = loader.load()
            if docs is None:
                print("获取不到内容")
                continue
            print(f"获取到内容: {docs}")

            doc = str(docs[0].page_content)
            doc = doc.replace("\n", " ")
            update_company_website_info(company_id, doc)
        except BaseException as e:
            print(f"googleSearchAgent 链接 {website} 获取不到内容")
            print(e)


if __name__ == "__main__":
    print("load website begin")
    run()

    print("load website end")
