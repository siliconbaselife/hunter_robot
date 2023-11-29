import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from dao.manage_dao import login_check_db, manage_account_register
import json
def generate_email_code():
    code = ""
    for i in range(4):
        code += str(random.randint(0, 9))

    return code


def send_verify_email(email, code):
    con = smtplib.SMTP_SSL('smtp.gmail.com', 465)

    con.login('aistormy2049@gmail.com', 'spnjosyxgljlrthi')

    msg = MIMEMultipart()
    subject = Header('AIStormy verify code', 'utf-8').encode()
    msg['Subject'] = subject
    msg['From'] = 'aistormy2049@gmail.com <aistormy2049@gmail.com>'
    msg['To'] = email
    text = MIMEText('verify code: {}'.format(code), 'plain', 'utf-8')
    msg.attach(text)

    con.sendmail('aistormy2049@gmail.com', email, msg.as_string())
    con.quit()


def user_register(passwd, email):
    res = login_check_db(email)
    if len(res) > 0 :
        return 1, "user_name already used"
    config = {"group_msg":"beijing"}
    c_j = json.dumps(config)
    desc = '线上注册'
    manage_account_register(passwd, email, desc, c_j)
    return 0, ""

def user_verify_email(email):
    res = login_check_db(email)
    if len(res) > 0 :
        return 1, "user_name already used", ""

    code = generate_email_code()
    send_verify_email(email, code)
    return 0, "", code