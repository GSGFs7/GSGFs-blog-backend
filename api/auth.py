import json
import base64
import hashlib
import hmac
import time

import jwt
from django.conf import settings
from ninja.security import HttpBearer


class Auth(HttpBearer):
    def authenticate(self, request, token):
        try:
            # 解码 token
            decoded_token = base64.b64decode(token).decode("utf-8")
            token_data = json.loads(decoded_token)

            # 获取数据
            timestamp = token_data["timestamp"]
            nonce = token_data["nonce"]
            signature = token_data["signature"]

            # 验证时间戳
            current_time = int(time.time() * 1000)  # ms
            if current_time - timestamp > 60000:  # 一分钟
                return None

            # 复现签名
            message = f"{timestamp}.{nonce}"
            expected_signature = hmac.new(
                settings.API_KEY.encode(), message.encode(), hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                return True
            else:
                return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None


class TimeBaseAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            # 解码 token
            decoded_token = base64.b64decode(token).decode("utf-8")
            toke_data = json.loads(decoded_token)

            # 获取时间和消息
            current_time = int(time.time() / 10)  # 10s
            message = str(toke_data["message"])
            client_signature = str(toke_data["signature"])

            # 生成服务器端签名
            server_signature = self.generate_signature(current_time, message)
            server_signature1 = self.generate_signature(current_time - 1, message)

            # 验证
            if hmac.compare_digest(client_signature, server_signature):
                return True
            if hmac.compare_digest(client_signature, server_signature1):
                return True
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    @staticmethod
    def generate_signature(timestamp: int, message: str) -> str:
        hmac_obj = hmac.new(
            settings.API_KEY.encode(),
            str(timestamp).encode(),
            hashlib.sha256,
        )
        hmac_obj.update(message.encode())
        return hmac_obj.hexdigest()
