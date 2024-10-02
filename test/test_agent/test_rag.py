from service.llm_agent_service import *


def read_txts(path):
    with open(path, "r") as f:
        lines = f.read()

    txts = []
    token_num = 0
    txt = ""
    for line in lines:
        if len(line) == 0:
            if len(txt) > 0:
                txts.append(txt)
            token_num = 0
            txt = ""
        token_num += len(line)
        if token_num > 200:
            txts.append(txt)
            txt = ""
        txt += line
        token_num = len(txt)

    return txts


def read_txts_raw(path):
    with open(path, "r") as f:
        lines = f.read()

    txt_str = "".join(lines)
    return txt_str


if __name__ == "__main__":
    path = "/root/workspace/data/Abraham_Wise/msg.txt"
    txts = read_txts_raw(path)
    agent = EmbeddingAgent(txts)
    agent.cal("列举该人跟中国相关的时间")
