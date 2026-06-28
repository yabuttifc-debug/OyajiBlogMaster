import os
import anthropic

MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = (
    "あなたは小学校の保護者向けブログ記事を書くライターです。"
    "箕輪小学校おやじの会のブログに掲載する記事を書いてください。"
    "文体は親しみやすく、わかりやすい日本語で書いてください。"
    "出力はHTML形式（<p>、<h3>、<ul>/<li>タグを適宜使用）にしてください。"
    "HTMLの外側に余計なマークダウンや説明文を付けないでください。"
)


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY が設定されていません。"
            ".env ファイルまたは環境変数に ANTHROPIC_API_KEY を設定してください。"
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_draft(event_text: str, title_hint: str = "") -> str:
    client = _get_client()
    title_instruction = f'タイトルは「{title_hint}」にしてください。\n\n' if title_hint else ""
    user_message = (
        f"{title_instruction}"
        "以下のイベント情報をもとに、ブログ記事を作成してください。\n\n"
        f"【イベント情報】\n{event_text}"
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def edit_post_content(current_html: str, instructions: str) -> str:
    client = _get_client()
    user_message = (
        "以下のブログ記事HTMLを、指示に従って修正してください。"
        "修正後のHTMLのみを出力してください。説明文は不要です。\n\n"
        f"【修正指示】\n{instructions}\n\n"
        f"【現在の記事HTML】\n{current_html}"
    )
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text
