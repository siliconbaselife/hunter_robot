from service.tools_service import *

manage_account_id = 'clementhu.ZY@outlook.com'
platform = 'Linkedin'
def test():
    candidate_id = 'linkedin.com/in/remichenard'
    rows = get_resume_by_candidate_ids_and_platform(manage_account_id, platform, [candidate_id], 0, 1)
    r = rows[0][0]
    profile = parse_profile(r, 'need_deserialize', True)
    print(profile['age'])

if __name__ == '__main__':
    test()

