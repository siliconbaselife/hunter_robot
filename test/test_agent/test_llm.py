from service.llm_agent_service import *


def read_txts(path):
    with open(path, "r") as f:
        lines = f.readlines()

    txts = []
    txt = ""
    token_num = 0
    for line in lines:
        if len(line) == 0:
            if len(txt) > 0:
                txts.append(txt)
            txt = ""
            token_num = 0
        token_num += len(line)
        if token_num > 2000:
            txts.append(txt)
            txt = ""
        txt += line
        token_num = len(txt)

    return txts


if __name__ == "__main__":
    query = "列举该人跟中国相关的事件, 萃取出内容，按照时间顺序排列。"
    path = "/root/workspace/data/Abraham_Wise/msg.txt"

    txts = read_txts(path)
    extract_agent = extractionRelationAgent()
    content = ""
    for txt in txts:
        event_list = extract_agent.parse(txt, query)
        print(event_list)
        content += event_list["txt"] + "\n"

    summerize_agent = summarizeAgent()
    res = summerize_agent.get(content, query)
    print(res)
