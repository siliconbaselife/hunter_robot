def get_web_res_suc_with_data(data):
    return {'ret': 0, 'msg': 'success', 'data': data}

def get_web_res_fail(reason):
    return {'ret': -1, 'msg': 'fail', 'data': reason}
