from service.business_service import jd_match_service

jd = "1.AI领域销售 2.2年以上工作经验 3.有B端销售经验"

r = jd_match_service("lishundong2009@163.com", "linkedin.com/in/claire-tseng-0b6419187", jd)
print(r)

