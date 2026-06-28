# 箕輪小学校おやじの会 ブログ管理ツール

## プロジェクト概要

箕輪小学校おやじの会（神奈川県横浜市日吉）のBloggerブログを管理するPythonツール。
イベントレポートの作成・編集・投稿をClaudeと協力して行う。

- **ブログURL**: https://minowa-oyaji.blogspot.com/
- **ブログID**: `2902848606842221450`
- **認証**: `.env` の `MASTER_PASSWORD`（自分で決めた任意の文字列 / 対話入力不要）

---

## エージェント設計方針

### メインエージェント（Opus）の役割
- ユーザーの意図を理解し、作業計画を立てる
- サブエージェントへの指示と結果の確認・承認
- Blogger CLIコマンドの直接実行（list / show / apply-edit 等）
- 最終判断が必要な場面での意思決定

**メインは考える・監督する。繰り返し発生する実作業はすべてSonnetサブエージェントに委譲する。**

### サブエージェント（Sonnet）の役割

| スキル              | 担当作業                 | 起動タイミング   |
| ---------------- | -------------------- | --------- |
| `article-writer` | イベント情報からブログ記事HTMLを生成 | 新記事作成時    |
| `furigana-check` | HTMLの振り仮名を点検・修正      | 記事作成後・編集後 |
| `face-blur`      | 写真の顔を自動検出してぼかし加工     | 写真アップロード前 |
| `image-upload`   | 画像を一括アップロードしてURL取得   | 写真のURL取得時 |
| `discord-notify` | ブログ更新をDiscordサーバに通知  | 記事公開・更新後  |
| `reel-maker`     | ブログ内容からInstagramリール動画（縦9:16）を生成し、Google Driveに配置 | 記事公開後・SNS展開時 |

---

## 標準ワークフロー

### 新記事作成

```
1. [Opus]    イベント情報・写真の確認
2. [Sonnet]  face-blur    → 写真の顔ぼかし加工
3. [Sonnet]  image-upload → 画像URLを取得
4. [Sonnet]  article-writer → 記事HTML生成（article.html）
5. [Sonnet]  furigana-check → 振り仮名点検・修正
6. [Opus]    内容確認・承認
7. [Opus]    python blog_agent.py post-draft → Bloggerに下書き保存
8. [Opus]    Blogger管理画面で確認後、公開をユーザーに案内
9. [Sonnet]  discord-notify → DiscordサーバにブログURLを通知
```

### 既存記事の編集

```
1. [Opus]    python blog_agent.py show "タイトル" → current_post.html に取得
2. [Opus]    編集内容をユーザーと確認・適用
3. [Sonnet]  furigana-check → 振り仮名点検・修正
4. [Opus]    python blog_agent.py apply-edit → Bloggerに反映
```

### リール動画・SNS展開（ブログ公開後 / `reel-maker`）

ブログ記事を公開したら、その内容を紹介するInstagramリール動画を作り、Google Driveに配置する。

```
1. [Opus/Sonnet] ブログ本文 or イベント資料から要点を抽出（イベント名・流れ・次回告知など）
2. [Sonnet] reel-maker → 縦9:16(1080x1920)のリール動画を生成
            - 写真ベース（顔ぼかし済み写真を使用）   … reel_make.py をテンプレに
            - グラフィック告知（写真なし・テキスト演出）… reel_quest.py をテンプレに
3. [Sonnet] crf28 で軽量版(.mp4)を書き出し（スマホ送信・IG投稿用）
4. [Sonnet] Google Drive の親フォルダ配下にイベント別サブフォルダを作り、
            「動画(軽量版) + Instagram投稿テキスト(キャプション+タグ)」を配置
5. [Opus] ユーザーに案内（IGアプリで音楽を付けて投稿 / 下書き保存はスマホアプリのみ）
```

**技術メモ（reel-maker の実装）**
- 動画生成: `PIL`(フレーム描画) + `imageio` / `imageio-ffmpeg`（同梱ffmpeg）。Ken Burns風ズーム＋クロスフェード。
  日本語フォントは `C:\Windows\Fonts\BIZ-UDGothicB.ttc`。絵文字は画面内テキストに使わない（豆腐化するため）。
- 軽量化: `ffmpeg -crf 28 -preset slow -pix_fmt yuv420p -movflags +faststart`（45MB→数MBに）。
- 子どもの顔写真を使う場合は必ず `face-blur` 済みの画像を使用すること。
- Driveへの動画配置: **Webアップロードはネイティブのファイル選択ダイアログが壁で自動化不可**。
  代わりに **Googleドライブ デスクトップ版（`G:\マイドライブ\…`）の同期フォルダへファイルコピー**で設置する。
  フォルダ作成・テキスト/Googleドキュメントの作成はDrive連携(MCP)で可能（バイナリ動画は不可）。
- ハッシュタグ方針は「日本語・全国リーチ重視・5つ以内」（[[instagram-hashtag-policy]] 参照）。

---

## よく使うコマンド（Opusが直接実行）

```powershell
python blog_agent.py list                                        # 公開済み記事一覧
python blog_agent.py list-drafts                                 # 下書き一覧
python blog_agent.py show "記事タイトルの一部"                    # 記事HTML取得
python blog_agent.py apply-edit "タイトル" --file current_post.html  # 編集反映
python blog_agent.py post-draft --title "タイトル" --file article.html  # 下書き保存
python blog_agent.py extract event.pdf                           # 資料テキスト抽出
```

---

## 振り仮名ルール

```html
✅ <ruby>大会<rt>たいかい</rt></ruby>          漢字にはつける
✅ <ruby>綱引<rt>つなひ</rt></ruby>き          送り仮名はruby外に出す（漢字だけにrtをつける）
✅ <ruby>MVP<rt>えむぶいぴー</rt></ruby>       英字は子ども向けに例外でOK
❌ <ruby>レース<rt>れーす</rt></ruby>          カタカナにはつけない
❌ <ruby>ドッジボール<rt>どっじぼーる</rt></ruby>  カタカナにはつけない
❌ <ruby>綱引き<rt>つなひき</rt></ruby>        送り仮名をruby内に含めない
```

---

## 制約・禁止事項

### 🔴 子どもの顔写真は必ずぼかし加工をおこなう
- ブログに掲載する写真に子どもの顔が写っている場合、**必ず `face-blur` スキルでぼかし加工してからアップロードする**
- ぼかし未処理の写真を直接アップロードしてはならない
- 顔が検出されなかった画像はユーザーに目視確認を促す

### 🔴 記事の削除は自動で行わない
- 削除操作は必ず実行前にユーザーへ確認をとる
- 「古い記事を整理して」などの曖昧な指示では削除しない
- 削除は取り消しできないため慎重に対応する

---

## ファイル構成

```
OyajiBlogMaster/
├── blog_agent.py          メインCLI
├── modules/
│   ├── blogger.py         Blogger API操作
│   ├── crypto.py          認証情報の暗号化・復号
│   ├── document.py        PDF/Word テキスト抽出
│   ├── ai_writer.py       AI記事生成（Anthropic API）
│   └── face_blur.py       顔検出＋ぼかし処理（opencv + mediapipe）
├── creds/                 暗号化済み認証情報（Gitignore対象）
├── Image/                 アップロード前の画像置き場
├── current_post.html      編集中の記事HTML（一時ファイル）
├── article.html           新規作成中の記事HTML（一時ファイル）
├── .env                   環境変数（MASTER_PASSWORD, ANTHROPIC_API_KEY）
└── requirements.txt       依存ライブラリ
```

---

## 環境セットアップ

```powershell
pip install -r requirements.txt
```

初回のみ認証セットアップが必要：
```powershell
python blog_agent.py setup --secrets client_secrets.json
```

### 依存ライブラリ・必要なAPI

- 依存ライブラリは `requirements.txt` に集約（Blogger/Google API・cryptography・docx/pdfplumber/pptx・
  python-dotenv・requests・anthropic・opencv-python・pillow-heif・mediapipe）。
- 必要なAPI／認証情報と取得手順、他ツール（Codex/Copilot）での使い方は **`README.md`** に記載。
  - Google Blogger API（`client_secrets.json` を各自で取得）★必須
  - Anthropic API キー（AI記事生成を使う場合）/ Discord Webhook（通知を使う場合）
- 顔ぼかしの注意: `modules/face_blur.py` は mediapipe 0.10.30 以降では旧 `mp.solutions` API 廃止により
  動作しない。`mediapipe==0.10.14` に固定するか、OpenCV YuNet 実装に置き換える（詳細は README）。

### 他者への配布・共有時の注意（秘密情報）

このフォルダをそのまま渡すと認証情報が流出する。配布前に `.env` / `client_secrets.json` /
`creds/*.enc` / `creds/*.salt` / `Image/`（子どもの写真）を削除すること。詳細は `README.md` の
「共有・配布時の注意」を参照。
