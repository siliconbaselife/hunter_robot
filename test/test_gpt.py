from utils.gpt import GptChat
from algo.llm_inference import gpt_manager
from algo.llm_base_model import Prompt

if __name__ == "__main__":
    print("test gpt")
    # gpt_chat = GptChat()
    # message = {'user_message': 'hi'}
    # r = gpt_chat.generic_chat(message)
    # print(r)
    prompt_msg = f"lishundong \nThis is a LinkedIn resume of a candidate. As a headhunter, you need to analyze the resume " \
                 f"and summarize two aspects:\n1 => Industry Experience and Expertise\n2 => Career Highlights\nThe result should " \
                 f"be represented in JSON format with 'industry_experience' for industry experience and expertise, and 'career_highlights' for career highlights. " \
                 f"\nSummarize the content in no more than 50 words, and ensure it is within 50 words.\nThe result content is returned in Chinese." \
                 f"Ensure the output is a valid JSON object in a compact format without any additional explanations, escape characters, newline characters, or backslashes."
    prompt = Prompt()
    prompt.add_user_message(prompt_msg)
    output = gpt_manager.chat_task(prompt)
    print(output)

    print("test end")
