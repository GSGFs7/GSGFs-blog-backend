from io import BytesIO
from typing import IO

import blake3


def calculate_blake3_hash(
    data: IO | str | bytes,
    *,
    max_threads: int = 1,  # blake3 multi-thread acceleration
    used_for_security: bool = False,
) -> str:
    if isinstance(data, str):
        data: BytesIO = BytesIO(data.encode())
    elif isinstance(data, bytes):
        data: BytesIO = BytesIO(data)

    data.seek(0)
    hasher = blake3.blake3(max_threads=max_threads, usedforsecurity=used_for_security)
    while chunk := data.read(65536):
        hasher.update(chunk)
    return hasher.hexdigest()
