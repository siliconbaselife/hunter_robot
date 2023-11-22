import json
import openai
import requests
import os
import curlify

from algo.llm_base_model import Prompt
from utils.decorator import exception_retry,cost_time

from cryptography.fernet import Fernet

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY = cipher.decrypt(secret_token).decode()

OPENAI_PROXY = 'http://127.0.0.1:7890'


class ChatGPT:
    def __init__(self) -> None:
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
