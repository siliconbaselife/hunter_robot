from service.tools_service import search_profile_by_tag


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
    print(details)

if __name__ == '__main__':
    main()