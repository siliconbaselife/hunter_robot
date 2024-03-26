import google.generativeai as genai
import shortuuid

from utils.log import get_logger
from utils.config import config as config

logger = get_logger(config['log']['chat_log_file'])
genai.configure(api_key=config['llm']['gemini']['api_key'])

class Gemini(object):
    def __init__(self):
        self._id = shortuuid.uuid()
        self._safety_config = {
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        self._model = config['llm']['gemini']['model_type']
        self._chat = None
        logger.info(f'{self._id}| construct')

    @property
    def id(self):
        return self._id

    def send_message(self, prompt, temperature=0.4):
        if not self._chat:
            self._chat = genai.GenerativeModel(self._model).start_chat(history=[])
            logger.info(f'{self._id}| new chat')
        logger.info(f'{self._id}| user: --------------- {prompt}')
        gen_config = genai.types.GenerationConfig(temperature=temperature)
        response = self._chat.send_message(prompt, generation_config = gen_config, safety_settings = self._safety_config)
        response.resolve()
        msg = response.text
        logger.info(f'{self._id}| AI:   --------------- {msg}')
        return msg

_gemini_chat_center = {}

def get_gemini(chat_id=None):
    global _gemini_chat_center
    if chat_id is None:
        new_chat = Gemini()
        _gemini_chat_center[new_chat._id] = new_chat
        chat_id = new_chat._id
    return _gemini_chat_center[chat_id]
