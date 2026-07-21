import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key(secret):
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet():
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is required in server mode")
    return Fernet(_derive_fernet_key(secret))


def encrypt(plaintext, fernet=None):
    fernet = fernet or get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext, fernet=None):
    fernet = fernet or get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Cannot decrypt value: invalid token or wrong SECRET_KEY") from e
