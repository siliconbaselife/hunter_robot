from dao.tool_dao import insert_all_profile
from dao.tool_dao import update_all_profile
from dao.tool_dao import select_profile_hundred
from dao.tool_dao import select_all_profile_time

if __name__ == "__main__":
    print("begin transfer profile")
    id = 0

    while True:
        rows = select_profile_hundred(id)

        if len(rows) == 0:
            break

        id = rows[-1][0]
        profiles = []
        for row in rows:
            _, candidate_id, platform, raw_profile, cv_url, name, company, age, race, create_time = row
            if platform != "Linkedin":
                continue

            profiles.append({
                "candidate_id": candidate_id,
                "platform": platform,
                "raw_profile": raw_profile,
                "cv_url": cv_url,
                "name": name,
                "company": company,
                "age": age,
                "race": race,
                "create_time": create_time
            })
        print(f"get profiles {len(profiles)}")

        for profile in profiles:
            profile_time = select_all_profile_time(profile["create_time"])
            if profile_time is None:
                insert_all_profile(profile["candidate_id"], profile["platform"], profile["raw_profile"], profile["cv_url"], profile["name"], profile["company"], profile["age"], profile["race"], profile["create_time"])

            if profile_time >= profile["create_time"]:
                update_all_profile(profile["candidate_id"], profile["platform"], profile["raw_profile"], profile["cv_url"], profile["name"], profile["company"], profile["age"], profile["race"], profile["create_time"])
        break

    print("end")
