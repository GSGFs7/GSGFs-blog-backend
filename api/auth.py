import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from ninja.security import HttpBearer

logger = logging.getLogger()


# TODO: Auth,
#  1. multi-client and corresponding API key verification
#  2. fine-grained permissions: read/write
class TimeBaseAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            # decode token
            decoded_token = base64.b64decode(token).decode("utf-8")
            token_data = json.loads(decoded_token)

            # get payload
            nonce = str(token_data.get("nonce", ""))
            client_id = str(token_data.get("client_id", ""))
            client_signature = str(token_data.get("signature", ""))
            if not nonce or not client_id or not client_signature:
                return None

            # protect against replay attacks
            cache_key = self.generate_auth_token_cache_key(client_id, nonce)
            is_new_request = cache.add(cache_key, 1, timeout=30)  # atomicity
            if not is_new_request:
                return None

            # verify
            valid = False
            current_time_10s = int(time.time() / 10)  # 10s window
            for t in [current_time_10s, current_time_10s - 1]:
                server_sig = self.generate_signature(t, nonce, client_id)
                if hmac.compare_digest(client_signature, server_sig):
                    valid = True
                    break

            if valid:
                # get the 'client_id' in ninja api endpoint 'request.auth'
                return client_id
            return None
        except Exception as e:
            logger.debug(e)
            return None

    @staticmethod
    def generate_signature(timestamp: int, nonce: str, client_id: str) -> str:
        if settings.API_KEY is None:
            raise ValueError("API_KEY is not set")

        hmac_obj = hmac.new(
            settings.API_KEY.encode(),
            str(timestamp).encode(),
            hashlib.sha256,
        )
        hmac_obj.update(nonce.encode())
        hmac_obj.update(client_id.encode())
        return hmac_obj.hexdigest()

    @staticmethod
    def create_token(client_id: str, time_10s: Optional[int] = None) -> str:
        if time_10s is None:
            # may be floating point accuracy issues
            time_10s = int((time.time() * 1000 / 1000) / 10)

        nonce = uuid.uuid4().hex
        signature = TimeBaseAuth.generate_signature(time_10s, nonce, client_id)
        token_data = {
            "nonce": nonce,
            "client_id": client_id,
            "signature": signature,
        }
        token_json_str = json.dumps(token_data)
        return base64.b64encode(token_json_str.encode("utf-8")).decode("utf-8")

    @staticmethod
    def generate_auth_token_cache_key(client_id: str, nonce: str):
        return f"auth_token:{client_id}:{nonce}"
