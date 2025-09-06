from service.llm_agent_service import AmericanHRAgent
from dao.profile_dao import *
from dao.tool_dao import query_tag_filter_num_new
from service.tools_service import query_tag_filter_profiles_new, transfer_data_to_profiles


def get_hr_profiles():
    total_num = query_tag_filter_num_new("Clement.hu@tbirecruit.com", "Linkedin", "美国-洛杉矶-HR", None, None, None,
                                         None)
    all_profiles = []
    page_len = 50
    for i in range(int(total_num / page_len) + 1):

        rows = query_tag_filter_profiles_new("Clement.hu@tbirecruit.com", "Linkedin", "美国-洛杉矶-HR", None, None, None,
                                             None, None, None, None, i * page_len, page_len)
        profiles = transfer_data_to_profiles("Clement.hu@tbirecruit.com", "False", rows)
        for i, profile in enumerate(profiles):
            profile["profile"] = rows[i][1]
        all_profiles.extend(profiles)

    return all_profiles


def deal_profile(profile):
    candidate_id = profile["candidateId"]
    res = agent.cal(profile["profile"])
    profile_info = {
        "candidate_id": candidate_id,
        "age": -1 if res["age"] == "未知" else int(res["age"]),
        "name": profile["name"],
        "company": profile["department"],
        "chinese": res["chinese"],
        "graduate_school": res["graduate_school"],
        "education_background": res["education_background"],
        "work_year": -1 if res["age"] == "未知" else int(res["work_year"]),
        "work_location": res["work_location"],
        "HR_experience": res["HR_experience"],
        "labour_experience": res["labour_experience"],
        "oversea_experince": res["oversea_experince"]
    }
    add_american_hr_profile(profile_info)


if __name__ == "__main__":
    global agent
    print("开始做识别")
    profiles = get_hr_profiles()
    print(f"获取到 {len(profiles)} 份简历")
    agent = AmericanHRAgent()
    for profile in profiles:
        try:
            deal_profile(profile)
        except BaseException as e:
            print(e)
            print(traceback.format_exc())