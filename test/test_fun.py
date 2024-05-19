import json
import re
import traceback
import datetime
def cv_str(obj, dent):
    cv = ""
    if type(obj) == dict:
        for k in obj:
            if obj[k]:
                for _ in range(dent):
                    cv += '\t'
                cv += (k + ":")
                cv += cv_str(obj[k], dent + 1)
    elif type(obj) == list:
        for e in obj:
            cv += cv_str(e, dent + 1)
    elif type(obj) == str or type(obj) == int or type(obj) == float:
        cv += (str(obj) + '\n')
    return cv

def get_max_time_info(time_info_str, default_time):
    if not time_info_str:
        return default_time
    max_start_year = default_time
    times = re.findall(r'\d\d\d\d', time_info_str)
    for t in times:
        max_start_year = max(max_start_year, int(t))
    return max_start_year

def get_min_time_info(time_info_str, default_time):
    if not time_info_str:
        return default_time
    min_start_year = default_time
    times = re.findall(r'\d\d\d\d', time_info_str)
    for t in times:
        min_start_year = min(min_start_year, int(t))
    return min_start_year

def deserialize_raw_profile(raw_profile):
    while type(raw_profile) == tuple:
        raw_profile = raw_profile[0]
    if raw_profile is None or type(raw_profile) != str:
        print("[deserialize_raw_profile] raw profile not str")
        return None
    pattern = re.compile(r'•\s+')
    new_raw_profile = pattern.sub(' ', raw_profile)
    try:
        new_raw_profile = new_raw_profile.replace('\n', '\\n')
        if new_raw_profile.endswith('\\n'):
            new_raw_profile = new_raw_profile[:-2]
        return json.loads(new_raw_profile, strict=False)
    except BaseException as e:
        print(f"deserialize_raw_profile error: {new_raw_profile}")
        print(traceback.format_exc())
        return None

def parse_profile(profile):
    profile = deserialize_raw_profile(profile)
    if profile is None:
        return None
    res = {'candidateId' : None,
                 'department': None,
                 'lastCompany': None,
                 'title': None,
                 'lastTitle': None,
                 'last5Jump': None,
                 'name':None,
                 'location':None,
                 'contactInfo': None,
                 'cv':None,
                 'age': None,
                 'isChinese': None,
                 'languages': None}
    if 'id' in profile:
        res['candidateId'] = profile['id']
    if 'profile' in profile:
        profile = profile['profile']
    experience = profile['experiences'][0] if 'experiences' in profile and len(profile['experiences']) > 0 else None
    if experience and 'companyName' in experience:
        res['department'] = experience['companyName']
        res['lastCompany'] = experience['companyName']

    if 'role' in profile:
        res['title'] = profile['role']
    elif 'works' in experience and len(experience['works']) > 0:
        work = experience['works'][0]
        if 'workPosition' in work:
            res['role'] = work['workPosition']
    res['lastTitle'] = res['title']
    name = None
    if 'name' in profile:
        name = profile['name']
        res['name'] = profile['name']

    if 'location' in profile:
        res['location'] = profile['location']

    if 'contactInfo' in profile:
        res['contactInfo'] = cv_str(profile['contactInfo'], 0)
    if profile:
        res['cv'] = cv_str(profile, 0)
    if name:
        res['isChinese'] = False
        chs_names = ['Zhao', 'Qian', 'Sun', 'Li', 'Zhou', 'Wu', 'Zheng', 'Wang', 'Feng', 'Chen', 'Zhu', 'Wei', 'Shen', 'Han', 'Yang', 'Qin', 'You', 'Xu', 'He', 'Lv', 'Shi', 'Zhang', 'Kong', 'Cao', 'Yan', 'Hua', 'Jin', 'Tao', 'Jiang', 'Xie', 'Zou', 'Yu', 'Bo', 'Shui', 'Dou', 'Yun', 'SU', 'Pan', 'Ge', 'Fan', 'Peng', 'Lang', 'Lu', 'Chang', 'Ma', 'Miao', 'Feng', 'Hua', 'Fang', 'Yu', 'Ren', 'Yuan', 'Liu', 'Bao', 'Shi', 'Tang', 'Fei', 'Lian', 'Qin', 'Xue', 'Lei', 'He', 'Ni', 'Teng', 'Yin', 'Luo', 'Bi', 'Hao', 'Wu', 'An', 'Chang', 'Le', 'Yu', 'Fu', 'Pi', 'Qi', 'Kang', 'Bu', 'Gu', 'Meng', 'Ping', 'Huang', 'He', 'Mu', 'Xiao', 'Yin', 'Yao', 'Shao', 'Qi', 'Mao', 'Di', 'Mi', 'Bei', 'Ming', 'Zang', 'Ji', 'FU', 'Cheng', 'Dai', 'Song', 'Ji', 'Shu', 'Qu', 'Dong', 'Liang', 'Du', 'Lan', 'Min', 'Jia', 'Lou', 'Tong', 'Guo', 'Lin', 'Diao', 'Zhong', 'Qiu', 'Luo', 'Gao', 'Xia', 'Cai', 'Tian', 'Hu', 'Ling', 'Huo', 'Ling', 'Wan', 'Zhi', 'ke', 'Guan', 'Mo', 'Miao', 'Xie', 'Zong', 'Ding', 'Deng', 'Shan', 'Hang', 'Bao', 'Zuo', 'Cui', 'Niu', 'Weng', 'Xun', 'Yang', 'Hui', 'Gong', 'Cheng', 'Hua', 'Pei', 'Rong', 'Jiao', 'Mu', 'Gu', 'Che', 'Hou', 'Mi', 'Quan', 'Ban', 'Gong', 'Ning', 'Chou', 'Luan', 'Zu', 'Fu', 'Liu', 'Long', 'Ye', 'Si', 'Bai', 'Huai', 'Cong', 'Lai', 'Zhuo', 'Qiao', 'Shuang', 'Dang', 'Cui', 'Tan', 'Ran', 'Bian', 'Chai', 'Liao', 'Gong', 'Jian', 'Sha', 'You', 'Hai', 'Wen', 'Zhai', 'Kou', 'Rao', 'Pu', 'Ou', 'She', 'Nian', 'Ai', 'Ha', 'An', 'Zhan', 'Ruan', 'Bing', 'Tu', 'Zhuang', 'Geng', 'Guang', 'Chao', 'AH', 'AU', 'BIK', 'BING', 'BIT', 'BONG', 'BUN', 'CHAI', 'CHAK', 'CHAM', 'CHAN', 'CHANG', 'CHAT', 'CHAU', 'CHEN', 'CHENG', 'CHEONG', 'CHEUK', 'CHEUNG', 'CHI', 'CHIANG', 'CHICKC', 'HIGN', 'CHIK', 'CHIN', 'CHING', 'CHIT', 'CHIU', 'CHO', 'CHOI', 'CHOK', 'CHONG', 'CHOR', 'CHOW', 'CHOY', 'CHU', 'CHUEN', 'CHUI', 'CHUM', 'CHUN', 'CHUNG', 'DIK', 'DIU', 'FAT', 'FA', 'FAI', 'FAN', 'FANG', 'FEI', 'FO', 'FOG', 'FOK', 'FONG', 'FOO', 'FOOK', 'FOON', 'FORK', 'FU', 'FUI', 'FUK', 'FUNG', 'HING', 'HA', 'HAN', 'HANG', 'HAU', 'HEI', 'HEUNG', 'HIM', 'HIN', 'HIP', 'HIU', 'HO', 'HOHO', 'HOI', 'HOK', 'HON', 'HONG', 'HOU', 'HSU', 'HSUI', 'HUANG', 'HUEN', 'HUI', 'HUNG', 'HWANG', 'JIM', 'KA', 'KAI', 'KAK', 'KAM', 'KAN', 'KANG', 'KAR', 'KAU', 'KEI', 'KEUNG', 'KHOO', 'KIM', 'KIN', 'KING', 'KIT', 'KIU', 'KO', 'KOK', 'KON', 'KONG', 'KOON', 'KOT', 'KU', 'KUA', 'KUEN', 'KUI', 'KUK', 'KUN', 'KUNG', 'KUO', 'KWAI', 'KWAN', 'KWING', 'KWOK', 'KWONG', 'LAI', 'LAM', 'LAN', 'LAP', 'LARM', 'LAU', 'LAW', 'LEE', 'LEI', 'LEONG', 'LEUNG', 'LI', 'LIANG', 'LIAO', 'LIEW', 'LIK', 'LIM', 'LIN', 'LING', 'LIP', 'LIT', 'LIU', 'LO', 'LOI', 'LOK', 'LONG', 'LOO', 'LOOK', 'LOONG', 'LOW', 'LUEN', 'LUET', 'LUI', 'LUK', 'LUMLUN', 'LUN', 'LUNG', 'MA', 'MAK', 'MAN', 'MANG', 'MAO', 'MAR', 'MEI', 'MIN', 'MING', 'MIU', 'MO', 'MOK', 'MOOK', 'MOON', 'MUI', 'MUK', 'MUNG', 'NAM', 'NANG', 'NAR', 'NEI', 'NEUNG', 'NG', 'NGA', 'NGAI', 'NGAN', 'NGAU', 'NGO', 'NGON', 'NIE', 'NIN', 'NING', 'NUI', 'O', 'OI', 'ON', 'PAK', 'PANG', 'PAT', 'PAU', 'PEI', 'PIK', 'PIN', 'PING', 'PIU', 'PO', 'POK', 'PONG', 'POO', 'POON', 'PUI', 'PUN', 'SAI', 'SAM', 'SAN', 'SANG', 'SAU', 'SE', 'SECK', 'SEE', 'SEI', 'SEK', 'SHAN', 'SHE', 'SHEK', 'SHEUNG', 'SHI', 'SHIH', 'SHING', 'SHIU', 'SHP', 'SHU', 'SHUE', 'SHUEN', 'SHUK', 'SHUM', 'SHUN', 'SI', 'SIK', 'SIM', 'SIN', 'SING', 'SIT', 'SIU', 'SO', 'SUEN', 'SUET', 'SUI', 'SUM', 'SUN', 'SUNG', 'SZE', 'TAI', 'TAK', 'TAM', 'TAN', 'TANG', 'TAO', 'TAT', 'TAU', 'TIM', 'TIN', 'TING', 'TIP', 'TIT', 'TO', 'TONG', 'TSAM', 'TSANG', 'TSE', 'TSIM', 'TSO', 'TSOI', 'TSUI', 'TUEN', 'TUNG', 'TYE', 'UNG', 'VONG', 'WAH', 'WAI', 'WAN', 'WANG', 'WAT', 'WING', 'WO', 'WON', 'WONG', 'WOO', 'WOOD', 'WOON', 'WU', 'WUI', 'WUN', 'WUT', 'YAM', 'YAN', 'YANG', 'YAO', 'YAT', 'YAU', 'YEE', 'YEI', 'YEN', 'YEUK', 'YEUNG', 'YI', 'YICK', 'YIK', 'YIM', 'YIN', 'YING', 'YIP', 'YIU', 'YOUNG', 'YU', 'YUE', 'YUEN', 'YUET', 'YUI', 'YUK', 'YUNG', 'ZHANG']
        for split_name in name.split(' '):
            if ('\u4E00' <= split_name <= '\u9FFF') or ('\u3400' <= split_name <= '\u4DBF') or split_name in chs_names:
                res['isChinese'] = True
    # age
    if 'educations' not in profile or len(profile['educations']) == 0:
        if 'experiences' in profile:
            experiences = profile['experiences']
            min_start_year = 9999
            for experience in experiences:
                if 'timeInfo' in experience:
                    min_start_year = get_min_time_info(experience['timeInfo'], min_start_year)
            if min_start_year != 9999:
                start_age = 21
                duration = datetime.datetime.now().year - min_start_year
                if duration > 0:
                    age = start_age + duration
                    res['age'] = age
    else:
        educations = profile['educations']
        graduated_year = 1000
        for education in educations:
            if 'timeInfo' in education and education['timeInfo'] is not None and\
            (('majorInfo' in education and 'Masters degree' in education['majorInfo']) or ('degreeInfo' in education and 'Masters degree' in education['degreeInfo'])):
                graduated_year = get_max_time_info(education['timeInfo'], graduated_year)
                start_age = 23
            elif 'timeInfo' in education and education['timeInfo'] is not None:
                graduated_year = get_max_time_info(education['timeInfo'], graduated_year)
                start_age = 21
        if graduated_year != 1000:
            res['age'] = start_age + datetime.datetime.now().year - graduated_year
    if 'languages' in profile and len(profile['languages']) > 0:
        res['languages'] = cv_str(profile['languages'], 0)

    if 'experiences' in profile and len(profile['experiences']) > 0:
        experiences = profile['experiences']
        last_5_jump = 0
        start_year = datetime.datetime.now().year - 5
        for experience in experiences:
            print(experience['timeInfo'])
            if 'timeInfo' in experience and experience['timeInfo'] != None and type(experience['timeInfo']) == str:
                if (get_max_time_info(experience['timeInfo'], 1000)) > start_year:
                    last_5_jump += 1
        res['last5Jump'] = last_5_jump
    return res

def main():
    with open('/Users/db24/tmp/dumps/dump.data', 'r') as f:
        lines = f.readlines()

    for line in lines:
        p = parse_profile(line)
        print(json.dumps(p))

if __name__ == '__main__':
    main()