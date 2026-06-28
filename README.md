# OyajiBlogMaster — 小学校おやじの会 ブログ管理ツール

Blogger ブログのイベントレポートを、AIコーディングエージェント（Claude Code / Codex / GitHub Copilot など）と協力して
作成・編集・投稿するための Python ツールです。記事HTMLの生成、振り仮名付け、写真の顔ぼかし、画像アップロード、
Discord通知までを CLI（`blog_agent.py`）と各モジュールで行います。

> このツールは特定のブログ専用ではありません。**Google Cloud のOAuth認証情報と自分のBloggerブログを用意すれば、
> 誰でも自分のブログ用に使えます。** 受け取った方は下記「セットアップ」を実施してください。

---

## 1. 必要なもの（前提）

| 種別 | 内容 | 必須/任意 |
| --- | --- | --- |
| Python | 3.10 以上（開発・動作確認は 3.12） | 必須 |
| Google アカウント | Blogger ブログを所有していること | 必須 |
| Google Cloud プロジェクト | Blogger API 有効化 + OAuth クライアント | 必須 |
| Anthropic API キー | AI記事生成（`ai_writer`）を使う場合 | 任意 |
| Discord Webhook URL | 更新をDiscord通知する場合 | 任意 |

---

## 2. 必要なライブラリ

Python 3.10 以上が必要です。すべて `requirements.txt` に記載済みなので、まとめて入れられます。

```bash
pip install -r requirements.txt
```

用途ごとに整理した一覧です（「必須/任意」は、その機能を使うかどうかの目安）。

### 2-1. コア（ブログ操作）★必須

| ライブラリ | 用途 |
| --- | --- |
| google-api-python-client | Blogger API v3 の操作 |
| google-auth-oauthlib / google-auth-httplib2 | Google OAuth 認証 |
| cryptography | 認証情報の暗号化保存（`creds/`） |
| python-dotenv | `.env` の環境変数読み込み |
| requests | HTTP通信（画像アップロード・Discord通知） |

### 2-2. 資料テキスト抽出（任意 / `extract`）

| ライブラリ | 用途 |
| --- | --- |
| pdfplumber | PDF からテキスト抽出 |
| python-docx | Word(.docx) からテキスト抽出 |
| python-pptx | PowerPoint(.pptx) からテキスト抽出 |

### 2-3. AI記事生成（任意 / `ai_writer`）

| ライブラリ | 用途 |
| --- | --- |
| anthropic | Claude API で記事HTMLを生成（要 ANTHROPIC_API_KEY） |

### 2-4. 写真の顔ぼかし（任意 / `face-blur`）

| ライブラリ | 用途 |
| --- | --- |
| opencv-python | 顔検出（YuNet）＋ぼかし処理。numpy を同梱 |
| pillow-heif | iPhone写真(HEIC)の読み込み。Pillow(PIL) を同梱 |
| mediapipe | 旧実装の顔検出（※下記「顔ぼかしの注意点」参照。新版では非推奨） |

### 2-5. リール動画生成（任意 / `reel-maker`）

| ライブラリ | 用途 |
| --- | --- |
| imageio | フレーム列から mp4 を書き出し |
| imageio-ffmpeg | ffmpeg バイナリを同梱（別途ffmpegのインストール不要） |
| Pillow (PIL) | 動画フレームの描画（文字・図形）。pillow-heif 経由で導入される |
| numpy | フレームの数値処理。opencv-python 経由で導入される |

> 💡 リール動画は写真の顔ぼかし機能と組み合わせて使うため、`opencv-python` / `pillow-heif` も必要です。
> ffmpeg は `imageio-ffmpeg` に同梱されるので、OSへの別インストールは不要です。

---

## 3. 必要なAPI・認証情報の取得手順

### 3-1. Google（Blogger API）★必須

1. [Google Cloud Console](https://console.cloud.google.com/) で新規プロジェクトを作成。
2. 「APIとサービス」→「ライブラリ」で **Blogger API v3** を有効化。
3. 「OAuth同意画面」を構成（外部・テストユーザーに自分のGoogleアカウントを追加）。
4. 「認証情報」→「OAuthクライアントID」を作成。アプリの種類は **デスクトップアプリ**。
5. 生成されたJSONを **`client_secrets.json`** という名前でこのフォルダ直下に保存。
6. 自分のブログIDを調べておく（Blogger管理画面のURL、または `python blog_agent.py list` 実行後の案内）。

### 3-2. Anthropic API キー（任意）

[Anthropic Console](https://console.anthropic.com/) で発行し、`.env` の `ANTHROPIC_API_KEY` に設定。
使用モデルは `modules/ai_writer.py` の `MODEL`（既定 `claude-sonnet-4-6`）。

### 3-3. Discord Webhook（任意）

Discordサーバ設定 →「連携サービス」→「ウェブフック」で作成し、URLを `.env` の `DISCORD_WEBHOOK_URL` に設定。

---

## 4. セットアップ手順

```bash
# 1) ライブラリをインストール
pip install -r requirements.txt

# 2) .env を用意（雛形をコピーして自分の値を記入）
cp .env.example .env
#   ANTHROPIC_API_KEY   … 任意（AI生成を使う場合）
#   MASTER_PASSWORD     … 認証情報を暗号化する任意のパスワード（自分で決める）
#   DISCORD_WEBHOOK_URL … 任意（Discord通知を使う場合）

# 3) client_secrets.json をフォルダ直下に配置（手順3-1で取得）

# 4) 初回認証セットアップ（ブラウザでGoogleログイン→creds/ に暗号化保存）
python blog_agent.py setup --secrets client_secrets.json

# 5) 自分のブログIDを設定
#   CLAUDE.md 冒頭の「ブログID」と、必要に応じて modules/blogger.py を自分のIDに変更
```

> `MASTER_PASSWORD` を対話入力なしで使いたい場合は `.env` に記載します。
> 暗号化された認証情報は `creds/` に保存され、`.gitignore` で共有対象外になっています。

---

## 5. 使い方（主なコマンド）

```bash
python blog_agent.py list                                         # 公開済み記事一覧
python blog_agent.py list-drafts                                  # 下書き一覧
python blog_agent.py show "記事タイトルの一部"                     # 記事HTMLを current_post.html に取得
python blog_agent.py post-draft --title "タイトル" --file article.html   # 下書き保存
python blog_agent.py apply-edit "タイトル" --file current_post.html      # 編集を反映
python blog_agent.py extract event.pdf                            # 資料テキスト抽出
python blog_agent.py upload-image                                 # 画像アップロードしてURL取得
```

記事作成のワークフロー・振り仮名ルールは **`CLAUDE.md`** に詳しく記載しています。
AIエージェント（Claude Code等）は `CLAUDE.md` を自動で読み込んで作業方針を把握します。

### Instagramリール動画の生成（`reel-maker`）

ブログ公開後、内容を紹介する縦型(9:16)のリール動画を生成できます（`pip install -r requirements.txt` 済みが前提）。

```bash
python reel_make.py     # 写真ベースのリール（顔ぼかし済み写真を使う）
python reel_quest.py    # 写真なしのグラフィック告知リール
```

- 出力は mp4。`imageio-ffmpeg` 同梱のffmpegで `-crf 28` の軽量版も書き出せます（スマホ送信・IG投稿用）。
- Google Drive への動画配置は、**Googleドライブ デスクトップ版の同期フォルダ（例: `G:\マイドライブ\…`）へ
  コピー**する方法が確実です（Web版/連携APIはバイナリ動画のアップロードができないため）。
- 詳細な手順・テンプレートの考え方は `CLAUDE.md` の「リール動画・SNS展開」を参照。

---

## 6. AIコーディングツールについて（ツール非依存）

このリポジトリは特定のAIツールに依存しません。

- **Claude Code** を使う場合: `CLAUDE.md` が自動で読み込まれ、ワークフロー・振り仮名ルール等が反映されます。
- **Codex / GitHub Copilot など** を使う場合: `CLAUDE.md` と本 `README.md` を、その都度コンテキスト（指示）として
  読み込ませてください（多くのツールはリポジトリ内のMarkdownを参照できます）。
- Python と CLI が動けば、AIツールなしでも `blog_agent.py` を手動で実行できます。

`.claude/` フォルダは Claude Code 用の補助設定です。他ツール利用時は無視して構いません。

---

## 7. 顔ぼかしの注意点（重要）

- 子どもの顔写真は **必ずぼかし加工してからアップロード** してください（`CLAUDE.md` の禁止事項参照）。
- `modules/face_blur.py` は **mediapipe の旧 `mp.solutions` API** を使っており、
  **mediapipe 0.10.30 以降では動作しません**。対処は次のいずれか:
  - `pip install "mediapipe==0.10.14"` で旧バージョンに固定する、または
  - OpenCV の **YuNet**（`opencv-python` 同梱の `cv2.FaceDetectorYN`）で検出する実装に置き換える
    （集合写真・小さい顔にも強く、HEIC対応もしやすい）。
- 顔が検出されなかった画像は、必ず人の目で確認してください。

---

## 8. ディレクトリ構成

```
OyajiBlogMaster/            ← このフォルダをプロジェクトのルートとして開いてください
├── README.md               本ファイル
├── CLAUDE.md               AIエージェント向けの作業方針・ワークフロー・振り仮名ルール
├── blog_agent.py           メインCLI
├── reel_make.py            リール動画生成（写真ベース）
├── reel_quest.py           リール動画生成（グラフィック告知）
├── requirements.txt        依存ライブラリ
├── .env.example            環境変数の雛形（コピーして .env を作る）
├── client_secrets.json     Google OAuth情報（★各自で用意・共有しない）
├── creds/                  暗号化済み認証情報（★共有しない / .gitignore対象）
├── modules/
│   ├── blogger.py          Blogger API操作
│   ├── crypto.py           認証情報の暗号化・復号
│   ├── document.py         PDF/Word/PPTX テキスト抽出
│   ├── ai_writer.py        AI記事生成（Anthropic API）
│   ├── face_blur.py        顔検出＋ぼかし
│   └── discord_notify.py   Discord通知
└── Image/                  アップロード前の画像置き場（個人情報を含むため共有しない）
```

---

## 9. 共有・配布時の注意（秘密情報）

このフォルダをそのまま渡すと、**あなたのGoogle/Anthropic/Discordの認証情報が流出します。**
配布前に必ず以下を削除・初期化してください（詳細は受け渡し時のチェックリスト参照）。

- `.env`（APIキー・パスワード・Webhook URL）
- `client_secrets.json`（Google OAuthシークレット）
- `creds/` 内の `*.enc` / `*.salt`（暗号化済みだが、あなたのブログへのアクセス権そのもの）
- `Image/` などの子どもの写真

`.gitignore` で上記はGit管理から除外済みです。Gitで配布する場合も、過去のコミット履歴に
残っていないか確認してください。
