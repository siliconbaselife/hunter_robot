from service.tools_service import search_profile_by_tag


def get_stability(detail):
    

def main():
    manage_account_id = '18870243977@163.com'
    platform = 'Linkedin'
    tags = ['菲律宾HR']
    page = 1
    limit = 10
    contact2str = True
    data, error_msg = search_profile_by_tag(manage_account_id, platform, tags, page, limit, contact2str)
    if error_msg is not None:
        print(f'{error_msg}')
        exit(1)
    details = data['details']
    titles = ['candidate_id', 'age', 'education', 'language', 'stability', 'industry', 'attributes', 'module', 'level']
    data  = []
    for detail in details:
        row = []
        if 'candidate_id' not in detail:
            continue
        row.append(detail['candidate_id'])
        row.append(str(detail['age']) if 'age' in detail and detail['age'] is not None else '不确定')
        row.append(str(detail['language']) if 'language' in detail and detail['language'] is not None else '不确定')


if __name__ == '__main__':
    main()