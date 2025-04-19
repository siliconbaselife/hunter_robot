from service.llm_agent_service import CompanyServiceOrProductType
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


if __name__ == "__main__":
    global agent
    print("开始做识别")
    profiles = get_catl_profiles()
    print(f"获取到 {len(profiles)} 份简历")
    company_agent = CompanyServiceOrProductType()
    function_infos = company_agent.cal("宁德时代")
    print(function_infos)
