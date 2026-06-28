import json
import tempfile
from pathlib import Path
import requests as req
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .crypto import CREDS_DIR, save_encrypted, load_encrypted, get_master_password

SCOPES = ["https://www.googleapis.com/auth/blogger"]
BLOG_ID = "2902848606842221450"
CLIENT_SECRETS_ENC = CREDS_DIR / "client_secrets.enc"
TOKENS_ENC = CREDS_DIR / "tokens.enc"


def setup(client_secrets_path: str, password: str) -> None:
    raw = Path(client_secrets_path).read_bytes()
    save_encrypted(raw, CLIENT_SECRETS_ENC, password)
    print(f"認証情報を暗号化して保存しました: {CLIENT_SECRETS_ENC}")
    _authorize(password)
    print("セットアップが完了しました。")


def _authorize(password: str) -> Credentials:
    raw = load_encrypted(CLIENT_SECRETS_ENC, password)
    client_config = json.loads(raw)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(client_config, f)
        tmp_path = f.name

    try:
        flow = InstalledAppFlow.from_client_secrets_file(tmp_path, SCOPES)
        creds = flow.run_local_server(port=0)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    _save_tokens(creds, password)
    return creds


def _save_tokens(creds: Credentials, password: str) -> None:
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }
    save_encrypted(json.dumps(token_data).encode(), TOKENS_ENC, password)


def _load_credentials(password: str) -> Credentials:
    raw = load_encrypted(TOKENS_ENC, password)
    data = json.loads(raw)
    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_tokens(creds, password)
    return creds


def get_service(password: str):
    if not TOKENS_ENC.exists():
        raise FileNotFoundError("トークンファイルが見つかりません。`python blog_agent.py setup` を先に実行してください。")
    creds = _load_credentials(password)
    return build("blogger", "v3", credentials=creds)


def list_posts(service, max_results: int = 20) -> list[dict]:
    result = service.posts().list(blogId=BLOG_ID, maxResults=max_results, status="LIVE").execute()
    items = result.get("items", [])
    return [{"id": p["id"], "title": p["title"], "url": p.get("url", "")} for p in items]


def list_drafts(service, max_results: int = 20) -> list[dict]:
    result = service.posts().list(blogId=BLOG_ID, maxResults=max_results, status="DRAFT").execute()
    items = result.get("items", [])
    return [{"id": p["id"], "title": p["title"]} for p in items]


def find_post_by_title(service, title: str) -> dict | None:
    for status in ("LIVE", "DRAFT"):
        result = service.posts().list(blogId=BLOG_ID, maxResults=50, status=status).execute()
        for p in result.get("items", []):
            if title in p["title"]:
                return {"id": p["id"], "title": p["title"], "url": p.get("url", "")}
    return None


def get_post_content(service, post_id: str) -> dict:
    return service.posts().get(blogId=BLOG_ID, postId=post_id, view="ADMIN").execute()


def update_post(service, post_id: str, title: str, content: str) -> dict:
    body = {"title": title, "content": content}
    return service.posts().update(blogId=BLOG_ID, postId=post_id, body=body).execute()


def create_draft(service, title: str, content: str) -> dict:
    body = {"title": title, "content": content}
    return service.posts().insert(blogId=BLOG_ID, body=body, isDraft=True).execute()


def upload_image(password: str, image_path: str) -> str:
    """画像を無料ホスティングサービス（catbox.moe）にアップロードして公開URLを返す。"""
    path = Path(image_path)
    ext = path.suffix.lower()
    content_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
    }.get(ext, "image/jpeg")

    with open(path, "rb") as f:
        response = req.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (path.name, f, content_type)},
            timeout=60,
        )

    response.raise_for_status()
    url = response.text.strip()
    if not url.startswith("https://"):
        raise ValueError(f"画像URLの取得に失敗しました。レスポンス: {url}")
    return url
