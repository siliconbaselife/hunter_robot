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
        company_id, linkedin_doc = row
        company_info = json.loads(linkedin_doc)
        company_info["company_id"] = company_id
        with open(os.path.join(dir, f"{i}.json")) as f:
            f.write(json.dumps(linkedin_doc))



