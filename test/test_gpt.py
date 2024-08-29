from utils.gpt import GptChat


if __name__ == "__main__":
    print("test gpt")
    gpt_chat = GptChat()
    message = {'user_message': 'hi'}
    r = gpt_chat.generic_chat(message)
    print(r)

    print("test end")