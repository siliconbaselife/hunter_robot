import json
import openai
import requests
import os
import curlify

from algo.llm_base_model import Prompt
from utils.decorator import exception_retry,cost_time

from cryptography.fernet import Fernet

from concurrent.futures import ThreadPoolExecutor
import threading
from utils.log import get_logger
from utils.config import config
import time


cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token_0 = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY_0 = cipher.decrypt(secret_token_0).decode()

secret_token_1 = "gAAAAABlaH0Znj77bm5n9luPszWTgtDYl74onM5l7zfswQESZqBKEexjJpSvpldN8HIY9ZbS_-p0ne8dlicFl8ckg_iI4kPI6E6pg-PMzCdF_thb1PfT4HCv5swyUzu9JZmEtXFVjyYJD4Bqu1EqAkSU9kzd802AQg=="
OPENAI_API_KEY_1 = cipher.decrypt(secret_token_1).decode()

OPENAI_PROXY = 'http://127.0.0.1:7890'



logger = get_logger(config['log']['log_file'])


class GPTManager:
    def __init__(self):
        logger.info(f"GPTManager init")
        self.pool = ThreadPoolExecutor(2)
        self.gpt_map = {
            "ThreadPoolExecutor-0_0": ChatGPT(OPENAI_API_KEY_0),
            "ThreadPoolExecutor-0_1": ChatGPT(OPENAI_API_KEY_1)
        }
    def exec_task(self, prompt):
        logger.info(f'chatgpt_exec {threading.current_thread().name}')
        chatgpt = self.gpt_map[threading.current_thread().name]
        return chatgpt.chat(prompt)
    def chat_task(self, prompt):
        f = self.pool.submit(self.exec_task, prompt)
        while not f.done():
            time.sleep(1)
        return f.result()

gpt_manager = GPTManager()


class ChatGPT:
    def __init__(self,OPENAI_API_KEY) -> None:
        openai.api_key = OPENAI_API_KEY
        if OPENAI_PROXY:
            openai.proxy = OPENAI_PROXY
    
    @exception_retry(retry_time=3, delay=2, failed_return=None)
    @cost_time
    def chat(self, prompt: Prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt.get_messages(),
            temperature=0.2
        )
        print(f"Total token: {response.usage.total_tokens}, cost ${response.usage.total_tokens / 1000 * 0.02}")
        return response.choices[0].message.content


class Vicuna:
    def __init__(self):
        pass

    def chat(self, prompt: Prompt):
        url = f'{os.getenv("VICUNA_API_URL")}/v1/chat/completions'
        payload = {
            'model': 'vicuna-7b',
            'messages': prompt.get_messages(),
            'temperature': 0.2
        }

        res = requests.post(url, json=payload)
        try:
            res_json = json.loads(res.text)
            return res_json.get('choices')[0].get('message').get('content')
        except Exception as e:
            print(
                f"没有返回正确的推理结果. \npayload = {payload} \ntoken_size = {prompt.get_token_size()} \nres.status = {res.status_code} \nres.context = {res.content} \n{curlify.to_curl(res.request)}")
            raise e
