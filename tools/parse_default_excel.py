import pandas as pd
import json
import io
import pyperclip


def generate_greeting(body):
    content = body.replace("\n", "\\n")
    content = content.replace("\'", "\\'")
    content = content.replace('\"', '\\"')
    return f"insert into default_greeting_template (platform, template) values('Linkedin', '{content}');"

def generate_email(subject, body):
    content = {'subject': subject, 'body': body}
    content = json.dumps(content, ensure_ascii=False)
    content = content.replace("\n", "\\n")
    content = content.replace("\'", "\\'")
    content = content.replace('\"', '\\"')
    return f"insert into default_email_template (platform, template) values('Linkedin', '{content}');"

def generate_inmail(subject, body):
    content = {'subject': subject, 'body': body}
    content = json.dumps(content, ensure_ascii=False)
    content = content.replace("\n", "\\n")
    content = content.replace("\'", "\\'")
    content = content.replace('\"', '\\"')
    return f"insert into default_inmail_template (platform, template) values('Linkedin', '{content}');"


excel_path = '/Users/db24/tmp/default.xlsx'
data_frame = pd.read_excel(excel_path)
types = data_frame['类型'].to_list()
subjects = data_frame['主题'].to_list()
bodies = data_frame['内容'].to_list()


string_builder = io.StringIO()
for idx in range(len(types)):
    tp = types[idx]
    subject = subjects[idx]
    body = bodies[idx]
    assert tp == 'greeting' or tp == 'inmail' or tp == 'email'
    if tp == 'greeting':
        sql = generate_greeting(body)
    elif tp == 'email':
        sql = generate_email(subject, body)
    else:
        sql = generate_inmail(subject, body)
    print(sql)
    print('=============')
    string_builder.write(sql)
    string_builder.write('\n')
sqls = string_builder.getvalue()
string_builder.close()
pyperclip.copy(sqls)