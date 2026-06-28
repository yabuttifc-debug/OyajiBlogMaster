"""Discord Webhook 通知モジュール"""
import os
import requests


def notify_blog_update(
    title: str,
    url: str,
    description: str = "",
    username: str = "箕輪小おやじの会ブログ",
    avatar_url: str = "",
) -> None:
    """
    ブログ更新をDiscordサーバに通知する。
    DISCORD_WEBHOOK_URL 環境変数が必要。
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError(
            "DISCORD_WEBHOOK_URL が設定されていません。"
            ".env ファイルに DISCORD_WEBHOOK_URL を設定してください。"
        )

    embed = {
        "title": title,
        "url": url,
        "description": description or "箕輪小学校おやじの会のブログが更新されました！",
        "color": 0xE53935,  # 赤
        "footer": {"text": "箕輪小学校おやじの会"},
    }

    payload = {
        "content": "📢 **ブログが更新されました！**",
        "embeds": [embed],
        "username": username,
    }
    if avatar_url:
        payload["avatar_url"] = avatar_url

    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
