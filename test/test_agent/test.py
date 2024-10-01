import os
import shutil
from dao.tool_data import query_tag_filter_profiles_new
from service.tools_service import parse_profile
from service.llm_agent_service import educationAgent
import json


def get_profiles():
    rows = query_tag_filter_profiles_new('lishundong2009@163.com', 'Linkedin', '1001测试', None, None, None, None,
                                         None, None, None, 0, 10)
    profiles = []
    for row in rows:
        profile = parse_profile(row[1], 'need_deserialize', False)
        profile["raw"] = json.loads(row[1])
        profiles.append(profile)

    return profiles


def parse_normal_info(profile):
    parsed_profile = {}
    parsed_profile["name"] = profile["name"]

    if "educations" in profile["raw"]["profile"] and len(profile["raw"]["profile"]["educations"]) > 0:
        education_agent = educationAgent()
        parsed_profile["学历"] = education_agent.get(profile["raw"]["profile"]["educations"])

    return parsed_profile


def show_end(profile):
    candidate_id = profile["candidate_id"]

    dir = './results'
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)

    profile_path = os.path.join(dir, candidate_id)
    profile_str = ""
    for key, value in profile.items():
        profile_str += "\n"
        profile_str += f"{key}:"
        if len(value) < 20:
            profile_str += value
        else:
            profile_str += "\n"
            profile_str += value
        profile_str += "\n"

    with open(profile_path, 'w') as f:
        f.write(profile_str)


if __name__ == "__main__":
    print("begin agent")
    profiles = get_profiles()
    for profile in profiles:
        parsed_profile = parse_normal_info(profile)
        print(parsed_profile)
        # show_end(parsed_profile)
    print("agent end")
