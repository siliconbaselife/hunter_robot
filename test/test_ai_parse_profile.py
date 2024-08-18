from service.tools_service import *

manage_account_id = 'lishundong2009@163.com'
platform = 'Linkedin'

if __name__ == '__main__':
    candidate_id = 'linkedin.com/in/liuneil'
    profile = parse_profile_by_ai_service(manage_account_id, platform, candidate_id, True)
    print(profile)

