
def process_profile(ori_profile):
    profile = ori_profile
    if profile[-1]=='/':
        profile = profile[:-1]
    return profile

def info_from_profile(profile):
    ## 'https://www.linkedin.com/in/zhouren'
    name = profile.split('/')[-1]
    lid = profile.split('www.')[-1]
    return name, lid
