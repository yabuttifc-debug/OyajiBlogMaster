import os
import getpass
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

CREDS_DIR = Path(__file__).parent.parent / "creds"
SALT_FILE = CREDS_DIR / "credentials.salt"


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_data(data: bytes, password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    return Fernet(key).encrypt(data), salt


def decrypt_data(encrypted: bytes, salt: bytes, password: str) -> bytes:
    key = derive_key(password, salt)
    return Fernet(key).decrypt(encrypted)


def save_encrypted(data: bytes, dest_path: Path, password: str) -> None:
    CREDS_DIR.mkdir(exist_ok=True)
    encrypted, salt = encrypt_data(data, password)
    dest_path.write_bytes(encrypted)
    SALT_FILE.write_bytes(salt)


def load_encrypted(src_path: Path, password: str) -> bytes:
    if not src_path.exists():
        raise FileNotFoundError(f"認証ファイルが見つかりません: {src_path}\n`python blog_agent.py setup` を先に実行してください。")
    if not SALT_FILE.exists():
        raise FileNotFoundError(f"ソルトファイルが見つかりません: {SALT_FILE}")
    return decrypt_data(src_path.read_bytes(), SALT_FILE.read_bytes(), password)


def get_master_password() -> str:
    password = os.environ.get("MASTER_PASSWORD")
    if password:
        return password
    return getpass.getpass("マスターパスワードを入力してください: ")
