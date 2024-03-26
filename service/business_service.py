from algo.gemini import get_gemini

def find_target_company(src_company, target_region, job, jd):
    prompt = f'公司 {src_company} 要在区域 {target_region} 内招聘的一个岗位 {job}，请给我合适的目标公司，需要以json的格式返回目标公司名字的列表。以下是岗位介绍：\n{jd}'
    llm = get_gemini()
    res_msg = llm.send_message(prompt=prompt)
    return llm.id, res_msg

def find_platform_keyword(job, jd, platform='领英'):
    prompt = f'匹配这个岗位 {job}，列出搜索简历跟业务相关的英文关键词，方便我在 {platform} 做搜索，需要以json格式返回关键词的列表。以下是岗位介绍\n{jd}'
    llm = get_gemini()
    res_msg = llm.send_message(prompt=prompt)
    return llm.id, res_msg
