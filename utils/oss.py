import oss2

ali_user_name = 'LTAI5tRAbpW9MNjDDnDAVCsq'
ali_pwd = '7RguIff46JiTrh43HkULgbXZPiIVqu'
auth = oss2.Auth(ali_user_name, ali_pwd)
# yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
# 填写Bucket名称。
bucket = oss2.Bucket(auth, 'oss-ap-southeast-1.aliyuncs.com', 'aistormy2023')


oss_url_prefix = "https://aistormy2023.oss-ap-southeast-1.aliyuncs.com/"
oss_url_prefix_delegate = "http://aistormy.com/vision/file/"


def generate_thumbnail(file_name, content):
    ret = bucket.put_object(file_name, content)
    return oss_url_prefix_delegate + file_name


if __name__ == "__main__":

    ali_user_name = 'LTAI5tRAbpW9MNjDDnDAVCsq'
    ali_pwd = '7RguIff46JiTrh43HkULgbXZPiIVqu'
    auth = oss2.Auth(ali_user_name, ali_pwd)
    # yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
    # 填写Bucket名称。
    bucket = oss2.Bucket(auth, 'oss-ap-southeast-1.aliyuncs.com', 'aistormy2023')


    oss_url_prefix = "https://aistormy2023.oss-ap-southeast-1.aliyuncs.com/"
    oss_url_prefix_delegate = "http://aistormy.com/vision/file/"

    with open('/Users/chenxutong/Desktop/art.pdf', 'r') as f:
        generate_thumbnail('art.pdf', f.read())