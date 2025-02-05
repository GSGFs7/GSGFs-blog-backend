import hashlib
import hmac
import time

import jwt
from django.conf import settings
from ninja.security import HttpBearer


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, "secret-key", algorithms=["HS256"])
            return payload
        except:
            return None


# class TimeBaseAuth(HttpBearer):
#     def authenticate(self, request, token):
#         try:
#             # 分离时间戳和签名
#             decoded = base64.b64decode(token).decode()
#             timestamp, signatrue = decoded.split(".")

#             current_time = int(time.time())

#             # 验证时间是否在5分钟内
#             if current_time - int(timestamp) > 300:
#                 return None

#             # 验证签名
#             expect_signature = self.generate_signature(timestamp)
#             if hmac.compare_digest(signatrue, expect_signature):
#                 print(signatrue)
#                 return True
#         except:
#             return None

#     @staticmethod
#     def generate_signature(timestamp):
#         message = str(timestamp).encode()
#         return hmac.new(
#             settings.API_KEY.encode(),
#             message,
#             hashlib.sha256,
#         ).hexdigest()


class TimeBaseAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            current_time = int(time.time() / 100)
            # print(token, current_time)

            if token == self.generate_signature(current_time):
                return True
            if token == self.generate_signature(current_time - 1):
                return True
        except:
            return None

    @staticmethod
    def generate_signature(timestamp):
        message = str(timestamp).encode()
        return hmac.new(
            settings.API_KEY.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
