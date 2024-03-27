import google.generativeai as genai

from utils.log import get_logger
from utils.config import config as config

genai.configure(api_key=config['llm']['gemini']['api_key'])

class Gemini(object):
    def __init__(self):
        self._safety_config = {
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        self._model = config['llm']['gemini']['model_type']
        self._chat = None

    def send_message(self, prompt, temperature=0.4):
        if not self._chat:
            self._chat = genai.GenerativeModel(self._model).start_chat(history=[])
        gen_config = genai.types.GenerationConfig(temperature=temperature)
        response = self._chat.send_message(prompt, generation_config = gen_config, safety_settings = self._safety_config)
        response.resolve()
        msg = response.text
        return msg

