import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from dao.manage_dao import login_check_db, manage_account_register
import json
from utils.log import get_logger
from utils.config import config

logger = get_logger(config['log']['log_file'])


def generate_email_code():
    code = ""
    for i in range(4):
        code += str(random.randint(0, 9))

    return code


def send_verify_email(email, code):
    con = smtplib.SMTP_SSL('smtp.163.com', 465)

    con.login('shadowhiring@163.com', 'YVNDIJOBSTVKLHQN')

    msg = MIMEMultipart()
    subject = Header('ShadowHiring verify code', 'utf-8').encode()
    msg['Subject'] = subject
    msg['From'] = 'shadowhiring@163.com <shadowhiring@163.com>'
    msg['To'] = email
    text = MIMEText('verify code: {}'.format(code), 'plain', 'utf-8')
    msg.attach(text)

    con.sendmail('shadowhiring@163.com', email, msg.as_string())
    con.quit()


def user_register(passwd, email, invite_account):
    res = login_check_db(email)
    if len(res) > 0:
        return 1, "user_name already used"
    config = {"group_msg": "beijing"}
    c_j = json.dumps(config)
    desc = '线上注册'
    manage_account_register(passwd, email, desc, c_j, invite_account)
    return 0, ""


def user_verify_email(email):
    logger.info(f"user_verify_email: {email}")
    res = login_check_db(email)
    logger.info(f"login_check_db res: {res}")
    if len(res) > 0:
        return 1, "user_name already used", ""

    code = generate_email_code()
    logger.info(f"generate_email_code: {code}")

    send_verify_email(email, code)
    logger.info(f"send_verify_email end")

    return 0, "", code



if __name__ == "__main__":
    send_verify_email('328564964@qq.com', '1111')