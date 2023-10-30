
def degree_compare(degree, min_degree):
    return True
    # degree_list = ['初中及以下', '中专', '高中', '大专', '本科', '硕士', '博士']
    # if '/' in degree:
    #     degrees = degree.split('/')
    #     for item_degree in degrees:
    #         if degree_compare(item_degree, min_degree):
    #             return True
    #     return False
    # else:
    #     degree_map = {degree: i for i, degree in enumerate(degree_list)} 
    #     return degree_map[degree] >= degree_map[min_degree]


def ensure_valid(raw_str):
    if type(raw_str) is not str:
        raw_str = ""
    return raw_str.replace("'", "").replace(" ", "")