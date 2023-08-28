from django.http import JsonResponse


class ApiResponse(JsonResponse):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data, *args, **kwargs)


class SuccessResponse(ApiResponse):
    def __init__(self, code=200, msg='success', data=None, *args, **kwargs):
        result = {'code': code, 'msg': msg}
        if data is not None:
            result['data'] = data
        super().__init__(result, *args, **kwargs)


class ErrorResponse(ApiResponse):
    def __init__(self, code, msg, data=None, *args, **kwargs):
        result = {'code': code, 'msg': msg}
        if data is not None:
            result['data'] = data
        super().__init__(result, *args, **kwargs)
