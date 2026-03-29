import base64
import hashlib
import logging
import uuid

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)


# TODO: Auth,
#  1. multi-client and corresponding API key verification
#  2. fine-grained permissions: read/write
class TimeBaseAuth(HttpBearer):
    """
    S2S authentication based on Fernet. TTL: 30s

    token format: client_id:nonce
    """

    async def authenticate(self, request, token):
        try:
            # fernet decrypt
            f = self.get_fernet()
            # TODO: put this to threading pool
            decrypt_token = f.decrypt(token.encode(), ttl=30).decode("utf-8")

            # get payload
            client_id, nonce = decrypt_token.split(":", 1)
            if not client_id or not nonce:
                return None

            cache_key = self.generate_auth_token_cache_key(client_id, nonce)
            # TODO: Auth, cache storage DOS protection
            is_new_request = await cache.aadd(cache_key, 1, timeout=30)  # atomicity
            if not is_new_request:
                # protect against replay attacks
                return None

            return client_id
        except Exception as e:
            # ban attackers?
            logger.debug(e)
            return None

    @staticmethod
    def create_token(client_id: str, nonce: str = None) -> str:
        if nonce is None:
            nonce = uuid.uuid4().hex

        f = TimeBaseAuth.get_fernet()
        payload = TimeBaseAuth.generate_token_format(client_id, nonce).encode("utf-8")
        return f.encrypt(payload).decode("utf-8")

    @staticmethod
    def generate_auth_token_cache_key(client_id: str, nonce: str):
        return f"auth_token:{client_id}:{nonce}"

    @staticmethod
    def generate_token_format(client_id: str, nonce: str):
        return f"{client_id}:{nonce}"

    @staticmethod
    def get_fernet():
        if not settings.API_KEY:
            raise ValueError

        key = hashlib.sha256(settings.API_KEY.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(key))
