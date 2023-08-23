def check_params(params, require_list):
    """
    检查参数
    """
    if not params and require_list:
        return {"code": 10000, "msg": "参数为空"}

    c = 200
    err_param = ""
    for item in require_list:
        if item not in params:
            c = 10001
            err_param = item
            break
        elif params.get(item) == "undefined":
            c = 10002
            err_param = item
            break
        elif params.get(item) == "":
            c = 10003
            err_param = item
            break

    result = {"code": c, "msg": "参数校验失败" if c != 200 else "success"}
    return result
