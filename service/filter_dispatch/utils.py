
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

degree_transfer_map = {
    "bachelor":"本科",
    "Bachelor":"本科",
    "master":"硕士",
    "Master":"硕士",
    "Doctor":"博士",
    "doctor":"博士",
    "Diploma":"大专",
    "diploma":"大专",
    "junior college":"大专",
    "juniorCollege":"大专",
    "highSchool":"高中",
    "high school":"高中",
    "cetificate":"中专",
    "Cetificate":"中专"
}

def degree_compare_v2(degree, min_degree):
    degree_list = ['NB','初中及以下', '中专', '高中', '大专', '本科', '硕士', '博士']
    degree_map = {d: i for i, d in enumerate(degree_list)} 
    if '/' in degree:
        degrees = degree.split('/')
        for item_degree in degrees:
            if ord(item_degree[0]) in (97,122) or ord(item_degree[0]) in (65,90):
                item_degree = degree_transfer_map.get(item_degree, 'NB')
            if degree_map[item_degree] >= degree_map[min_degree]:
                return True
        return False
    else:
        if ord(degree[0]) in (97,122) or ord(degree[0]) in (65,90):
            degree = degree_transfer_map.get(degree, 'NB')
        return degree_map[degree] >= degree_map[min_degree]

def ensure_valid(raw_str):
    if type(raw_str) is not str:
        raw_str = ""
    return raw_str.replace("'", "").replace(" ", "")