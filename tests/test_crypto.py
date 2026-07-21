import pytest

from app.crypto import decrypt, encrypt, get_fernet


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-value")


def test_encrypt_decrypt_roundtrip():
    fernet = get_fernet()
    ciphertext = encrypt("my-api-key", fernet=fernet)

    assert ciphertext != "my-api-key"
    assert decrypt(ciphertext, fernet=fernet) == "my-api-key"


def test_get_fernet_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        get_fernet()


def test_decrypt_invalid_token_raises_value_error():
    fernet = get_fernet()

    with pytest.raises(ValueError):
        decrypt("not-a-valid-token", fernet=fernet)
