
def degree_compare(degree, min_degree):
    degree_list = ['小学', '初中', '中专', '高中', '大专', '本科', '硕士', '博士']
    degree_map = {degree: i for i, degree in enumerate(degree_list)} 
    return degree_map[degree] >= degree_map[min_degree]