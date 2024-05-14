import requests

def test_profile_filter():
    params = {
        'platform': 'Linkedin',
        'conditions': {'age': {"min_age": 20, "max_age": 40}, 'is_chinese': True},
        'profile': '{"profile": {"contactInfo": {"url": "www.linkedin.com/in/qishuo-kia-zheng-7458b9195","Phone": "","Email": ""},'
                   '"name": "Qishuo(Kia) Zheng","location": "Guangzhou, Guangdong, China ","role": "中山大学学生","experiences": [{'
                   '"companyName": "腾讯","timeInfo": "Nov 2021 - Present · 2 yrs 7 mos","works": [{"workTimeInfo": "Nov 2021 - Present · 2 yrs 7 mos",'
                   '"workPosition": "产品策划"}]},{"companyName": "腾讯游戏","timeInfo": "Jun 2021 - Aug 2021 · 3 mos","works": [{'
                   '"workTimeInfo": "Jun 2021 - Aug 2021 · 3 mos","workPosition": "产品运营"}]},{"companyName": "玛氏食品",'
                   '"timeInfo": "Oct 2020 - Mar 2021 · 6 mos","works": [{"workTimeInfo": "Oct 2020 - Mar 2021 · 6 mos",'
                   '"workPosition": "AI & Automation Data Analyst Intern"}]},{"companyName": "数说故事DataStory","timeInfo": "May 2020 - Aug 2020 · 4 mos",'
                   '"works": [{"workTimeInfo": "May 2020 - Aug 2020 · 4 mos","worklocationInfo": "广州","workPosition": "Data Analyst Intern"'
                   '}]},{"companyName": "网易有道","timeInfo": "Sep 2019 - Jan 2020 · 5 mos","works": [{"workTimeInfo": "Sep 2019 - Jan 2020 · 5 mos",'
                   '"worklocationInfo": "广州","workPosition": "产品运营（数据分析方向）"}]}],"educations": [{"schoolName": "Sun Yat-sen University",'
                   '"majorInfo": "硕士学位, 应用统计","timeInfo": "2020 - 2022"},{"schoolName": "Sun Yat-sen University","majorInfo": "理科学士, 数学与应用数学",'
                   '"timeInfo": "2016 - 2020"}],"languages": []},"id": "www.linkedin.com/in/qishuo-kia-zheng-7458b9195"}'
    }

    r = requests.post('http://www.shadowhiring.cn/backend/tools/filterOnlineResume', json=params)
    print(f"results: {r.text}")


if __name__ == "__main__":
    print("开始测试linkedin filter api接口")
    test_profile_filter()
    print("测试完毕")