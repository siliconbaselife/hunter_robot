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
        print(profile)
        profile["raw"] = json.loads(row[1])
        profiles.append(profile)

    return profiles


def parse_normal_info(profile):
    parsed_profile = {}
    parsed_profile["name"] = profile["name"]
    parsed_profile["candidate_id"] = profile["candidateId"].split('/')[-1]
    parsed_profile["contact_info"] = profile["contactInfo"]

    if "educations" in profile["raw"]["profile"] and len(profile["raw"]["profile"]["educations"]) > 0:
        education_agent = educationAgent()
        parsed_profile["学历"] = education_agent.get(profile["raw"]["profile"]["educations"])

    if "experiences" in profile["raw"]["profile"] and len(profile["raw"]["profile"]["experiences"]) > 0:
        experience_agent = experienceAgent()
        parsed_profile["工作"] = experience_agent.get(profile["raw"]["profile"]["experiences"])

    return parsed_profile


def show_school(profile_str, educations):
    profile_str += "学历:\n"
    for education in educations:
        profile_str += f"   {education['学历']} {education['学校']} {education['时间']} \n"
    return profile_str


def show_experiences(profile_str, experiences):
    profile_str += "工作经历:\n"
    for experience in experiences:
        profile_str += f"   {experience['公司']} {experience['title']} {experience['时间']} \n"

    return profile_str


def show_contact(profile_str, contact_info):
    profile_str += "联系方式:\n"
    for key, value in contact_info.items():
        if key == "Email" and len(value) > 0:
            profile_str += f"   邮件: {value}\n"
        if key == "Phone" and len(value) > 0:
            profile_str += f"   电话: {value}\n"
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
    profile_str = show_experiences(profile_str, profile["工作"])
    profile_str = show_contact(profile_str, profile["contact_info"])

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
