
def process_profile(ori_profile):
    profile = ori_profile
    if profile[-1]=='/':
        profile = profile[:-1]
    return profile

def id_from_profile(profile):
    ## 'https://www.linkedin.com/in/zhouren'
    return profile.split('/')[-1]
