import inspect
import requests
from log.base import error


class PrintingServer(object):
    
    def __init__(self, host, api_key):
        self.host = host
        self.api_key = api_key
        self.headers = {"ApiKey": api_key}

    @staticmethod
    def submit(method, **kwargs):
        ref = inspect.currentframe().f_back.f_code.co_name
        try:
            resp = requests.request(method.upper(), **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            error("errors", f"[{ref}] error: {e}")
            return None

    def refresh_device_info(self, params):
        url = f'{self.host}/api/device/refresh_device_info'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=20)
        if resp is None:
            return {"code": 503, "msg": "刷新异常，请稍后再试"}

        return resp

    def refresh_printer_state(self, params):
        url = f'{self.host}/api/printer/refresh_printer_state'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=5)
        if resp is None:
            return {"code": 503, "msg": "刷新异常，请稍后再试"}

        return resp

    def get_printer_list(self, params):
        url = f'{self.host}/api/external_api/printer_list'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=5)
        if resp is None:
            return {"code": 503, "msg": "获取打印机列表失败，请稍后再试"}

        return resp

    def add_printing_job(self, post_data, job_files=None, api_key=None):
        url = f'{self.host}/api/print/job'
        headers = {'ApiKey': api_key} if api_key else self.headers
        resp = self.submit('POST', url=url, files=job_files, headers=headers, data=post_data, timeout=20)
        if resp is None:
            return {"code": 503, "msg": "打印异常，请稍后再试"}

        return resp

    def printer_params(self, params):
        url = f'{self.host}/api/print/printer_params'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "打印异常，请稍后再试"}

        return resp

    def printer_status(self, params):
        url = f'{self.host}/api/device/printer_status'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "打印异常，请稍后再试"}

        return resp

    def printer_dimension(self, post_data):
        url = f'{self.host}/api/print/printer_dimension'
        resp = self.submit('POST', url=url, headers=self.headers, json=post_data, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "打印异常，请稍后再试"}

        return resp

    def paper_dimension(self, params):
        url = f'{self.host}/api/print/paper_dimension'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "接口异常，请稍后再试"}

        return resp

    def paper_dimension_list(self, params):
        url = f'{self.host}/api/print/paper_dimension_list'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=60)
        if resp is None:
            return {"code": 503, "msg": "接口异常，请稍后再试"}

        return resp

    def job_result(self, params):
        url = f'{self.host}/api/print/job'
        resp = self.submit('GET', url=url, headers=self.headers, params=params, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "接口异常，请稍后再试"}

        return resp

    def revoke_job(self, params):
        url = f'{self.host}/api/print/job'
        resp = self.submit('DELETE', url=url, headers=self.headers, params=params, timeout=10)
        if resp is None:
            return {"code": 503, "msg": "接口异常，请稍后再试"}

        return resp

    def query_device_task(self, device_id, device_key, status=None):
        url = f'{self.host}/api/print/query_device_task'
        resp = self.submit(
            'POST', url=url, headers=self.headers,
            timeout=10, json={
                "deviceId": device_id,
                "deviceKey": device_key,
                "status": status
            })
        if resp is None:
            return {"code": 503, "msg": "接口异常，请稍后再试"}

        return resp
