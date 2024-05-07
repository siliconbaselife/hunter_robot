import json
import os

def f_extension_user_credit():
    os.system('mysql -h 127.0.0.1 -P 3306 -u chat_user -p"1" recruit_data_v2 -e "insert into extension_user_credit (user_id, user_credit) select user_id, user_credit from extension_user;"')

def f_extension_user_link():
    os.system('mysql -h 127.0.0.1 -P 3306 -u chat_user -p"1" recruit_data_v2 -e "select user_id, already_contacts from extension_user" > extension_user.txt')
    lines=[i[:-1] for i in open('extension_user.txt').readlines()]
    sql_list = []
    for l in lines[1:]:
        uid, contacts = l.split('\t')
        if contacts=='[]':
            continue
        contacts = json.loads(contacts)
        for pf, cttype in contacts:
            _, lid = info_from_profile(pf)
            sql = f"insert into extension_user_link (user_id, link_linkedin_id, link_contact_type) values ('{uid}', '{lid}', '{cttype}');"
            if sql in sql_list:
                print(f'WArNING: dup sql: {sql}')
                continue
            sql_list.append(sql)
    with open('extension_user_link.sql', 'w') as f:
        for sql in sql_list:
            f.write(f'{sql}\n')
    os.system('mysql -h 127.0.0.1 -P 3306 -u chat_user -p"1" recruit_data_v2 -e "source extension_user_link.sql"')

def info_from_profile(profile):
    ## 'https://www.linkedin.com/in/zhouren'
    name = profile.split('/')[-1]
    lid = profile.split('www.')[-1]
    return name, lid

if __name__=='__main__':
    f_extension_user_credit()
    # f_extension_user_link()