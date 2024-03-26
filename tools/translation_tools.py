import requests
import sys

_translation_tool = None

class BaiduTranslation(object):
    app_id=56377804
    api_key="3wmqpkVRlia09UPlYOVrq8fc"
    secret_key="aTBNvJgJFbdva93AifcgIsJbSgLlNZls"
    translate_url="https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1"
    token_url="https://aip.baidubce.com/oauth/2.0/token"

    def run(self, src_txt, src_lang="en", dst_lang="zh"):
        access_token = self._access_token()
        url = self.translate_url+ "?access_token="+ access_token
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        payload = {'q': src_txt, 'from': src_lang, 'to': dst_lang, 'termIds' : ""}
        r = requests.post(url, params=payload, headers=headers)
        print(r.text)
        result = r.json()
        # print(result)
        try:
            return "\n".join([item["dst"] for item in result["result"]["trans_result"]])
        except BaseException as e:
            assert False, f"translation abnormal, return: {result}"

    def _access_token(self):
        r = requests.post(self.token_url, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }, params= {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }, data="")

        assert r.status_code==200, f"request for access token failed for {r.status_code}, {r.text}"
        res = r.json()
        assert "access_token" in res, f"request for access token return abnormal: {res}"
        return res["access_token"]

def get_translation_tool():
    global _translation_tool
    if _translation_tool is None:
        _translation_tool = BaiduTranslation()
    
    return _translation_tool

if __name__=="__main__":
    src_txt = sys.argv[1]
    src_lang = "en"
    dst_lang = "zh"
    if len(sys.argv) > 2:
        assert len(sys.argv) == 4, "usage: python xxx.py src_txt src_lang dst_lang"
        src_lang = sys.argv[2]
        dst_lang = sys.argv[3]
    result = get_translation_tool().run(src_txt, src_lang=src_lang, dst_lang=dst_lang)
    print(f"translate {src_txt} ({src_lang}) to {result} ({dst_lang})")
