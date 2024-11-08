from service.tools_service import parse_profile_by_ai_service

if __name__ == "__main__":
    print("parse profile")
    manage_account_id = "lishundong2009@163.com"
    platform = "Linkedin"
    candidate_id = "linkedin.com/in/xun-golden-guo"
    use_ai = True
    language = "English"
    profile = parse_profile_by_ai_service(manage_account_id, platform, candidate_id, use_ai, language)
    print(profile)
