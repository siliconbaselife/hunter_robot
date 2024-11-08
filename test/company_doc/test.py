from service.tools_service import save_company_service

if __name__ == "__main__":
    print("company doc")
    tag = "test"
    company_id = "test.com"
    linkedin_doc = '{"overview": "test", "website": "test.com", "industry": "test", "company_size": "18 person", ' \
                   '"headquaters": "China", "Founded": "2020", "specialties": "test"}'
    save_company_service(tag, company_id, linkedin_doc)
