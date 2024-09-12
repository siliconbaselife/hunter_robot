
import base64
import requests
from json import dumps, loads
from utils.log import get_logger
from utils.config import config

import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from dao.tool_dao import create_google_account, query_google_account, delete_google_account, get_google_account, get_resume_by_candidate_ids_and_platform
from service.tools_service import deserialize_raw_profile

from email.message import EmailMessage

logger = get_logger(config['log']['log_file'])

CLIENT_SECRETS_FILE = './file/google_auth/web_client_secret.json' # secret json文件相对路径
SCOPES = [
    'openid', # 将您与您在 Google 上的个人信息关联起来
    'https://www.googleapis.com/auth/userinfo.email', # 查看您 Google 帐号的主电子邮件地址
    'https://www.googleapis.com/auth/userinfo.profile', # 查看您的个人信息，包括您已公开的任何个人信息
    # 'https://www.googleapis.com/auth/gmail.readonly', # 读取所有资源及其元数据，无写入操作。
    'https://www.googleapis.com/auth/gmail.send', # 仅发送信息。没有对邮箱的读取或修改权限。
]

def authorize_on_google(redirect_uri):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    # 这次的重定向链接
    flow.redirect_uri = redirect_uri
    # flow.redirect_uri = url_for(endpoint = "tools_web.oauth2callback", _external=True)
    # 拿到授权链接 和 state
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='select_account consent'
    )
    return authorization_url, state

def get_credentials_on_google(state, redirect_uri ,authorization_response):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials
    

def get_userinfo_by_credentials(credentials):
    credentials_dict = None
    if isinstance(credentials, str):
        credentials_dict = credentials_json_to_instance(credentials)
    else:
        credentials_dict = credentials
    user_info = build(
        serviceName='oauth2', version='v2', credentials=credentials_dict
    ).userinfo().get().execute()
    return user_info

# def credentials_to_dict(credentials):
#     return {
#         'token': credentials.token,
#         'refresh_token': credentials.refresh_token,
#         'token_uri': credentials.token_uri,
#         'client_id': credentials.client_id,
#         'client_secret': credentials.client_secret,
#         'scopes': credentials.scopes,
#         'expiry': credentials.expiry
#     }

# 获取用户的凭证信息列表
def get_accounts(manage_account_id):
    logger.info(
        "[backend_tools] get accounts by manage_account_id = {}".format(manage_account_id)
    )
    return query_google_account(manage_account_id)

def get_account_by_openid(openid, manage_account_id):
    logger.info(
        "[backend_tools] get accounts by openid = {} and manage_account_id = {}".format(openid, manage_account_id)
    )
    return get_google_account(openid= openid, manage_account_id = manage_account_id)

# 新增或更新
def create_account(manage_account_id, user_info, credentials):
    logger.info(
        "[backend_tools] create account by manage_account_id = {}, user_info = {}, credentials".format(manage_account_id, user_info, credentials)
    )
    if manage_account_id is None:
        return None, f'未登录'
    elif user_info is None:
        return None, f'没有用户信息'
    elif credentials is None:
        return None, f'没有用户凭证信息'
    id = user_info['id']
    email = user_info['email']
    name = user_info['name']
    picture = user_info['picture']
    create_google_account(openid=id, manage_account_id=manage_account_id,name=name,picture=picture,google_account_email=email,credentials=credentials)
    
    return id, None

def revoke_account(openid, manage_account_id):
    logger.info(
        "[backend_tools] revoke_account by openid = {} and manage_account_id = {}".format(openid, manage_account_id)
    )
    account_infos = get_account_by_openid(openid=openid, manage_account_id = manage_account_id)
    if len(account_infos) == 0:
        return None, f'{openid} 无对应账号记录'
    credentials_json = account_infos[0][5]
    credentials = credentials_json_to_instance(credentials_json=credentials_json)
    token = credentials.token
    error_msg = revoke_token(token)
    if error_msg is not None:
        return None, error_msg
    delete_google_account(openid, manage_account_id)
    return None, None
    # account_info = account_infos[0]
    # credentials = credentials_json_to_instance(account_info[5])
    # service = build("oauth2", "v2", credentials=credentials)

def revoke_token(token):
    logger.info(
        "[backend_tools] revoke_token by token = {}".format(token)
    )
    url = 'https://oauth2.googleapis.com/revoke'
    payload = {'token': token}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)
    logger.info(
        "[backend_tools] revoke_token by token = {} response status_code = {} text = {}".format(token, response.status_code, response.text)
    )
    if response.status_code == 200:
        return None
    else:
        logger.info(
            "[backend_tools] revoke_token by token = {} fail, response = {}".format(token, response.json())
        )
        return response.text


# 将凭证json转为凭证实例
def credentials_json_to_instance(credentials_json):
    logger.info(
        "[backend_tools] credentials_json_to_instance by credentials_json = {}".format(credentials_json)
    )
    if isinstance(credentials_json, Credentials):
        return credentials_json
    else: 
        return Credentials.from_authorized_user_info(loads(credentials_json), scopes=SCOPES)
    
def create_message(sender, to, subject, message_text):
    logger.info(
        "[backend_tools] create_message by sender = {}, to = {}, subject = {}, message_text = {}".format(sender, to, subject, message_text)
    )
    message = EmailMessage()
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject
    message.set_content(message_text)
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": encoded_message}

def send_message_by_gmail(manage_account_id, openid, platform, candidate_id, title, content, email_to):
    logger.info(
        "[backend_tools] send_message by manage_account_id = {}, openid = {}, platform = {}, candidate_id = {}, title = {}, content = {}, email_to = {}".format(manage_account_id, openid, platform, candidate_id, title, content, email_to)
    )
    # 这段跟tools_service.send_email_content一样
    if email_to is None:
        rows = get_resume_by_candidate_ids_and_platform(manage_account_id, platform, [candidate_id], 0, 10)
        if len(rows) == 0:
            return None, f'{candidate_id} 无对应记录'
        profile = deserialize_raw_profile(rows[0][1])
        if profile and 'profile' in profile:
            profile = profile['profile']
        logger.info('[send_email] profile = {} , candidate_id = {}'.format(profile, candidate_id))
        if not profile or 'contactInfo' not in profile or 'Email' not in profile['contactInfo'] or len(
                profile['contactInfo']['Email']) == 0:
            return None, f'{candidate_id} 无email联系方式'
        email_to = profile['contactInfo']['Email']
    account_infos = get_account_by_openid(openid=openid, manage_account_id = manage_account_id)
    if len(account_infos) == 0:
        return None, f'{openid} 无对应账号记录'
    account_info = account_infos[0]
    email_from = account_info[4]
    
    try:
        message = create_message(email_from, email_to, title, content)
        credentials = credentials_json_to_instance(account_info[5])
        service = build("gmail", "v1", credentials=credentials)
        send_message_operate = (
            service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )
        message_id = send_message_operate["id"]
        logger.info(
            "[backend_tools] send_message_operate id = {}".format(message_id)
        )
        return message_id, None
    except HttpError as error:
        logger.error(
            "create_message error = {}".format(error.error_details)
        )
        return None, error.error_details
    
    
    