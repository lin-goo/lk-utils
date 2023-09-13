import json
import base64

from Crypto.Cipher import AES


class WXBizDataCrypt:
    """小程序数据解密"""

    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    @staticmethod
    def _unpad(s):
        return s[: -ord(s[len(s) - 1:])]

    def decrypt(self, encryptedData, iv):
        # base64 decode
        session_key = base64.b64decode(self.sessionKey)
        encrypted_data = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)
        cipher = AES.new(session_key, AES.MODE_CBC, iv)
        decrypted = json.loads(self._unpad(cipher.decrypt(encrypted_data)))

        if decrypted["watermark"]["appid"] != self.appId:
            raise Exception("Invalid Buffer")

        return decrypted
