def format_time(time_obj):
    f_str = '%Y-%m-%d %H:%M:%S'
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
