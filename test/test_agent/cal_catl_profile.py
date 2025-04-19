from service.llm_agent_service import CompanyServiceOrProductType, catlPeopleAgent
from dao.profile_dao import *
from dao.tool_dao import query_tag_filter_num_new
from service.tools_service import query_tag_filter_profiles_new, transfer_data_to_profiles


def get_catl_profiles():
    total_num = query_tag_filter_num_new("lishundong2009@163.com", "Linkedin", "宁德时代-US", None, None, None, None)
    all_profiles = []
    page_len = 50
    for i in range(int(total_num / page_len) + 1):
        rows = query_tag_filter_profiles_new("lishundong2009@163.com", "Linkedin", "宁德时代-US", None, None, None,
                                             None, None, None, None, i * page_len, page_len)
        profiles = transfer_data_to_profiles("lishundong2009@163.com", "False", rows)
        for i, profile in enumerate(profiles):
            profile["profile"] = rows[i][1]
        all_profiles.extend(profiles)

    return all_profiles


def deal_profile(profile, befores, middles, afters):
    candidate_id = profile["candidateId"]
    res = agent.cal(profile["profile"], befores, middles, afters)
    profile_info = {
        "candidate_id": candidate_id,
        "age": -1 if res["age"] == "无法判断" else int(res["age"]),
        "name": profile["name"],
        "company": profile["department"],
        "chinese": "yes" if res["chinese"] else "no",
        "graduate_school": res["graduate_school"],
        "education_background": res["education_background"],
        "school_level": res["school_level"],
        "five_years_jump_times": profile["last5Jump"],
        "function_type": res["function_type"],
        "service_country": res["service_country"],
        "rank_of_position": res["rank_of_position"],
        "profile": profile["profile"]
    }
    add_catl_profile(profile_info)


if __name__ == "__main__":
    global agent
    print("开始做识别")
    profiles = get_catl_profiles()
    print(f"获取到 {len(profiles)} 份简历")
    company_agent = CompanyServiceOrProductType()
    agent = catlPeopleAgent()
    befores, middles, afters = company_agent.cal("宁德时代")
    for profile in profiles:
        try:
            deal_profile(profile, befores, middles, afters)
        except BaseException as e:
            print(e)
            print(traceback.format_exc())
