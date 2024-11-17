from langchain_community.document_loaders import WebBaseLoader
from dao.tool_dao import update_company_website_info
from dao.tool_dao import query_company_infos
from dao.tool_dao import update_company_website_info
import json
import time

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run():
    company_infos = query_company_infos()
    for company_info in company_infos:
        company_id = company_info["company_id"]
        print(f"company_id: {company_id}")
        linkedin_doc = company_info["linkedin_doc"]
        linkedin_doc = linkedin_doc[1:]
        linkedin_doc = linkedin_doc[:-1]

        website_doc = company_info["website"]
        print(website_doc)
        if website_doc is not None:
            print("已经有网页内容")
            continue

        linkedin_info = json.loads(linkedin_doc)
        website = linkedin_info["website"]
        print(f"website: {website}")
        begin = time.time()
        try:
            try_time = 0
            while try_time < 3:
                try:
                    loader = WebBaseLoader(website)
                    loader.requests_kwargs = {'verify': False, "timeout": 10}
                    try_time += 1
                    docs = loader.load()
                except BaseException as e:
                    print(f"第 {try_time} 次获取不到")

            if docs is None:
                print(f"获取不到内容 cost: {time.time() - begin}")
                continue

            doc = str(docs[0].page_content)
            doc = doc.replace('\\', ' ')
            doc = doc.replace("\n", " ")
            doc = doc.replace("\'", " ")
            doc = doc.replace("\"", " ")

            update_company_website_info(company_id, doc)
            print(f"获取到内容 更新成功 cost: {time.time() - begin}")
        except BaseException as e:
            print(f"googleSearchAgent 链接 {website} 获取不到内容")
            print(e)


if __name__ == "__main__":
    print("load website begin")
    run()

    print("load website end")
