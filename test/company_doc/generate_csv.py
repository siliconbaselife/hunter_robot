import json
import shutil
import os
from dao.tool_dao import query_all_company_info

if __name__ == "__main__":
    print("generate csv")
    rows = query_all_company_info()

    dir = "companys"
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)

    for i, row in enumerate(rows):
        company_id, linkedin_doc, website_doc = row
        # print(linkedin_doc)
        # linkedin_doc = linkedin_doc.replace('\n', '\\n')
        # linkedin_doc = linkedin_doc.replace('\\"', ' ')
        # linkedin_doc = linkedin_doc.replace('\\', '')
        linkedin_doc = linkedin_doc[1:]
        linkedin_doc = linkedin_doc[:-1]

        print(company_id)
        print(linkedin_doc)

        company_info = json.loads(linkedin_doc, strict=False)
        company_info["company_id"] = company_id
        company_info["website"] = website_doc
        with open(os.path.join(dir, f"{i}.json"), 'w') as f:
            f.write(json.dumps(linkedin_doc))



