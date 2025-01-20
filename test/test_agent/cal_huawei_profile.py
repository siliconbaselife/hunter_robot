from service.llm_agent_service import huiweiPeopleAgent
from dao.profile_dao import *
from dao.tool_dao import query_tag_filter_profiles_new, query_tag_filter_num_new
from service.tools_service import query_tag_filter_profiles_new, transfer_data_to_profiles


def get_huawei_profiles():
    total_num = query_tag_filter_num_new("lishundong2009@163.com", "Linkedin", "huawei-法国", None, None, None, None)
    all_profiles = []
    page_len = 50
    for i in range(int(total_num / page_len) + 1):
        rows = query_tag_filter_profiles_new("lishundong2009@163.com", "Linkedin", "huawei-法国", None, None, None,
                                             None, None, None, None, i, page_len)
        profiles = transfer_data_to_profiles("lishundong2009@163.com", "False", rows)
        for i, profile in enumerate(profiles):
            profile["profile"] = rows[i][1]
        all_profiles.extend(profiles)

    return all_profiles


def deal_profile(profile):
    candidate_id = profile["candidateId"]
    f = is_huawei_exist(candidate_id)
    if f:
        print(f"{candidate_id} already insert")
        return
    print(f"{candidate_id} deal")

    res = agent.cal(profile["profile"])
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
        "service_or_product_type": res["service_or_product_type"],
        "function_type": res["function_type"],
        "service_country": res["service_country"],
        "rank_of_position": res["rank_of_position"],
        "department": res["department"],
        "cooperative_department": res["cooperative_department"],
        "profile": profile["profile"]
    }

    add_profile(profile_info)


if __name__ == "__main__":
    global agent

    print("开始做识别")
    profiles = get_huawei_profiles()
    agent = huiweiPeopleAgent()
    print(f"获取到 {len(profiles)} 份简历")
    for profile in profiles[:50]:
        deal_profile(profile)

    print("识别完成")
