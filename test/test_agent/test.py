import os
import shutil
from dao.tool_dao import query_tag_filter_profiles_new
from service.tools_service import parse_profile
from service.llm_agent_service import *
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
    parsed_profile["candidate_id"] = profile["candidateId"].split('/')[-1]

    if "educations" in profile["raw"]["profile"] and len(profile["raw"]["profile"]["educations"]) > 0:
        education_agent = educationAgent()
        parsed_profile["学历"] = education_agent.get(profile["raw"]["profile"]["educations"])

    if "experiences" in profile["raw"]["experiences"] and len(profile["raw"]["profile"]["experiences"]) > 0:
        experience_agent = experienceAgent()
        parsed_profile["工作"] = experience_agent.get(profile["raw"]["profile"]["experiences"])

    return parsed_profile


def show_school(profile_str, educations):
    profile_str += "学历:\n"
    for education in educations:
        profile_str += f"   {education['学历']} {education['学校']} {education['时间']} \n"
    return profile_str


def show_end(dir, profile):
    candidate_id = profile["candidate_id"]

    profile_path = os.path.join(dir, candidate_id)
    profile_str = ""
    profile_str += f"姓名: {profile['name']}\n"
    # for key, value in profile.items():
    #     profile_str += "\n"
    #     profile_str += f"{key}:"
    #     if len(value) < 20:
    #         profile_str += value
    #     else:
    #         profile_str += "\n"
    #         profile_str += value
    #     profile_str += "\n"
    profile_str = show_school(profile_str, profile["学历"])

    with open(profile_path, 'w') as f:
        f.write(profile_str)


if __name__ == "__main__":
    print("begin agent")
    profiles = get_profiles()
    dir = './results'
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)
    for profile in profiles:
        parsed_profile = parse_normal_info(profile)
        print(parsed_profile)
        show_end(dir, parsed_profile)
    print("agent end")
