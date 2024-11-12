import json

from dao.tool_dao import query_all_company_info

if __name__ == "__main__":
    print("generate csv")
    rows = query_all_company_info()

    lines = []
    for row in rows:
        company_id, linkedin_doc = row
        lines.append(f"{company_id}, {json.dumps(linkedin_doc)}")

    with open("1.csv", 'w') as f:
        f.write('\n'.join(lines))
