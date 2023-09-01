def format_time(time_obj, f_str='%Y-%m-%d %H:%M:%S'):
    return time_obj.strftime(f_str)


def deal_json_invaild(data):
    data = data.replace(' ','')
    data = data.replace("\n", "\\n").replace("\r", "\\r").replace("\n\r", "\\n\\r") \
        .replace("\r\n", "\\r\\n") \
        .replace("\t", "\\t")
    data = data.replace('":"', '&&testPassword1&&')\
        .replace('":', '&&testPassword2&&')\
        .replace('","', "$$testPassword$$")\
        .replace('{"', "@@testPassword@@")\
        .replace('"}', "**testPassword**")
    # print(data)

    data = data.replace('"', r'\"')\
        .replace('&&testPassword1&&', '":"').replace('&&testPassword2&&','":').replace('$$testPassword$$', '","').replace('@@testPassword@@', '{"').replace('**testPassword**', '"}')
    # print(data)
    return data


school_211 = '["北京大学","清华大学","复旦大学","上海交通大学","浙江大学","国防科技大学","中国人民大学","南京大学","中国科学技术大学","北京航空航天大学","同济大学","北京理工大学","东南大学","武汉大学","华中科技大学","哈尔滨工业大学","西安交通大学","南开大学","北京师范大学","华东师范大学","电子科技大学","中山大学","天津大学","厦门大学","华南理工大学","四川大学","西北工业大学","山东大学","重庆大学","中南大学","吉林大学","湖南大学","兰州大学","大连理工大学","中国农业大学","东北大学","中国海洋大学","中央民族大学","西北农林科技大学","郑州大学","云南大学","新疆大学","上海财经大学","北京邮电大学","中央财经大学","对外经济贸易大学","上海外国语大学","西安电子科技大学","中国政法大学","北京外国语大学","空军军医大学","北京交通大学","南京航空航天大学","南京理工大学","上海大学","西南财经大学","北京科技大学","华东理工大学","中国传媒大学","海军军医大学","北京工业大学","中南财经政法大学","河海大学","天津医科大学","苏州大学","东华大学","西南交通大学","华中师范大学","暨南大学","华北电力大学","南京师范大学","哈尔滨工程大学","武汉理工大学","陕西师范大学","华南师范大学","合肥工业大学","北京化工大学","中央音乐学院","西南大学","江南大学","东北师范大学","安徽大学","西北大学","福州大学","河北工业大学","北京林业大学","湖南师范大学","中国药科大学","北京中医药大学","中国地质大学（武汉）","南京农业大学","中国矿业大学（北京）","长安大学","中国矿业大学","中国石油大学（北京）","中国石油大学（华东）","海南大学","大连海事大学","南昌大学","华中农业大学","中国地质大学（北京）","辽宁大学","太原理工大学","贵州大学","北京体育大学","延边大学","广西大学","东北林业大学","四川农业大学","内蒙古大学","东北农业大学","宁夏大学","青海大学","石河子大学","西藏大学"]'
school_985 = '["北京大学","清华大学","上海交通大学","复旦大学","浙江大学","国防科技大学","中国科学技术大学","中国人民大学","南京大学","北京航空航天大学","北京理工大学","哈尔滨工业大学","西安交通大学","南开大学","同济大学","武汉大学","华中科技大学","北京师范大学","东南大学","四川大学","华东师范大学","电子科技大学","中山大学","天津大学","厦门大学","华南理工大学","西北工业大学","山东大学","重庆大学","中南大学","吉林大学","兰州大学","大连理工大学","中国农业大学","中国海洋大学","中央民族大学","湖南大学","东北大学","西北农林科技大学"]'
def is_211(school):
    return school in school_211

def is_985(school):
    return school in school_985

degree_dict = {
    "博士后": 4,
    "博士": 3,
    "硕士": 2,
    "本科": 1,
    "大专": 0,
    "高中": -1,
    "中专": -2,
    "初中及以下": -3
}
def get_degree_num(degree_str):
    return degree_dict[degree_str]



def encrypt(text, key):
    encrypted_text = ""
    for char in text:
        if char.isalpha():
            shift = 65 if char.isupper() else 97
            encrypted_char = chr((ord(char) - shift + key) % 26 + shift)
        else:
            encrypted_char = char
        encrypted_text += encrypted_char
    return encrypted_text

def decrypt(encrypted_text, key):
    decrypted_text = ""
    for char in encrypted_text:
        if char.isalpha():
            shift = 65 if char.isupper() else 97
            decrypted_char = chr((ord(char) - shift - key) % 26 + shift)
        else:
            decrypted_char = char
        decrypted_text += decrypted_char
    return decrypted_text


key = 3
original_text = "Hello, World!"
encrypted_text = encrypt(original_text, key)
decrypted_text = decrypt(encrypted_text, key)

print("原始文本:", original_text)
print("加密后:", encrypted_text)
print("解密后:", decrypted_text)