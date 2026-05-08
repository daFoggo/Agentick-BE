import secrets


def get_rand_hash(length: int = 16) -> str:
    if length <= 0:
        raise ValueError("length must be greater than 0")
    # token_hex(n) returns 2*n characters, so round up for odd lengths.
    nbytes = (length + 1) // 2
    return secrets.token_hex(nbytes)[:length]
