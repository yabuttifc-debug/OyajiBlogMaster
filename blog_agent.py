import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ワークフロー概要:
#
# [下書き作成]
#   Step1: python blog_agent.py extract event.pdf  → テキストをファイルに保存
#   Step2: ClaudeCode で記事HTMLを生成し article.html に保存してもらう
#   Step3: python blog_agent.py post-draft --title "タイトル" --file article.html
#
# [投稿編集]
#   Step1: python blog_agent.py show "投稿タイトル"  → 現在のHTMLをファイルに保存
#   Step2: ClaudeCode に修正指示を与えて edited.html に保存してもらう
#   Step3: python blog_agent.py apply-edit "投稿タイトル" --file edited.html


def cmd_setup(args):
    from modules.crypto import get_master_password
    from modules import blogger

    if not Path(args.secrets).exists():
        print(f"エラー: {args.secrets} が見つかりません。")
        sys.exit(1)

    password = get_master_password()
    blogger.setup(args.secrets, password)


def cmd_list(args):
    from modules.crypto import get_master_password
    from modules import blogger

    password = get_master_password()
    service = blogger.get_service(password)
    posts = blogger.list_posts(service)

    if not posts:
        print("投稿が見つかりませんでした。")
        return

    print(f"{'No.':<4} {'タイトル':<40} {'ID'}")
    print("-" * 70)
    for i, post in enumerate(posts, start=1):
        print(f"{i:<4} {post['title'][:40]:<40} {post['id']}")


def cmd_list_drafts(args):
    from modules.crypto import get_master_password
    from modules import blogger

    password = get_master_password()
    service = blogger.get_service(password)
    drafts = blogger.list_drafts(service)

    if not drafts:
        print("下書きが見つかりませんでした。")
        return

    print(f"{'No.':<4} {'タイトル':<40} {'ID'}")
    print("-" * 70)
    for i, post in enumerate(drafts, start=1):
        print(f"{i:<4} {post['title'][:40]:<40} {post['id']}")


def cmd_extract(args):
    """イベント資料からテキストを抽出してファイルに保存する（下書き作成 Step1）"""
    from modules import document

    file_path = args.file
    print(f"ドキュメントを読み込み中: {file_path}")
    event_text = document.extract_text(file_path)

    output_file = Path(file_path).stem + "_extracted.txt"
    Path(output_file).write_text(event_text, encoding="utf-8")

    print(f"\n抽出完了 → {output_file}\n")
    print("=" * 60)
    preview = event_text[:400] + ("..." if len(event_text) > 400 else "")
    print(preview)
    print("=" * 60)
    print(f"""
次のステップ:
  1. ClaudeCode に以下のように依頼してください:
       「{output_file} の内容をもとに、おやじの会ブログ用の記事HTMLを作成して
        article.html に保存してください」
  2. 生成されたら次を実行:
       python blog_agent.py post-draft --title "記事タイトル" --file article.html
""")


def cmd_post_draft(args):
    """ClaudeCodeで生成したHTMLをBloggerに下書きとして保存する（下書き作成 Step3）"""
    from modules.crypto import get_master_password
    from modules import blogger

    html_file = Path(args.file)
    if not html_file.exists():
        print(f"エラー: {args.file} が見つかりません。")
        sys.exit(1)

    html_content = html_file.read_text(encoding="utf-8")
    title = args.title

    password = get_master_password()
    service = blogger.get_service(password)

    print("Bloggerに下書きを保存中...")
    result = blogger.create_draft(service, title, html_content)
    print(f"\n下書きを作成しました: {result['title']}")
    print(f"管理URL: https://www.blogger.com/blog/post/edit/2902848606842221450/{result['id']}")


def cmd_show(args):
    """既存投稿のHTMLを取得してファイルに保存する（投稿編集 Step1）"""
    from modules.crypto import get_master_password
    from modules import blogger

    title_query = args.title
    password = get_master_password()
    service = blogger.get_service(password)

    print(f"「{title_query}」を検索中...")
    post = blogger.find_post_by_title(service, title_query)
    if not post:
        print(f"エラー: 「{title_query}」を含む投稿が見つかりませんでした。")
        sys.exit(1)

    full_post = blogger.get_post_content(service, post["id"])
    current_html = full_post.get("content", "")

    output_file = "current_post.html"
    Path(output_file).write_text(current_html, encoding="utf-8")

    print(f"\n投稿のHTMLを保存しました: {output_file}")
    print(f"タイトル: {full_post['title']}")
    print(f"""
次のステップ:
  1. ClaudeCode に以下のように依頼してください:
       「current_post.html を [修正内容] に従って修正して edited.html に保存してください」
  2. 修正されたら次を実行:
       python blog_agent.py apply-edit "{title_query}" --file edited.html
""")


def cmd_apply_edit(args):
    """ClaudeCodeで修正したHTMLをBloggerの投稿に反映する（投稿編集 Step3）"""
    from modules.crypto import get_master_password
    from modules import blogger

    title_query = args.title
    html_file = Path(args.file)

    if not html_file.exists():
        print(f"エラー: {args.file} が見つかりません。")
        sys.exit(1)

    new_html = html_file.read_text(encoding="utf-8")
    password = get_master_password()
    service = blogger.get_service(password)

    print(f"「{title_query}」を検索中...")
    post = blogger.find_post_by_title(service, title_query)
    if not post:
        print(f"エラー: 「{title_query}」を含む投稿が見つかりませんでした。")
        sys.exit(1)

    full_post = blogger.get_post_content(service, post["id"])

    print("Bloggerに更新中...")
    blogger.update_post(service, post["id"], full_post["title"], new_html)
    print(f"\n投稿を更新しました: {full_post['title']}")
    print(f"URL: {post['url']}")


def cmd_upload_image(args):
    """画像をBloggerにアップロードしてURLを取得する。"""
    from modules.crypto import get_master_password
    from modules import blogger

    image_path = Path(args.file)
    if not image_path.exists():
        print(f"エラー: {args.file} が見つかりません。")
        sys.exit(1)

    password = get_master_password()
    print(f"画像をアップロード中: {image_path.name} ...")
    image_url = blogger.upload_image(password, str(image_path))
    print(f"\n画像URLを取得しました:\n{image_url}")
    return image_url


def main():
    parser = argparse.ArgumentParser(
        description="おやじの会ブログ管理エージェント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
【下書き作成フロー】
  1. python blog_agent.py extract event.pdf           # テキスト抽出
  2. ClaudeCode で article.html を生成
  3. python blog_agent.py post-draft --title "タイトル" --file article.html

【投稿編集フロー】
  1. python blog_agent.py show "投稿タイトル"          # 現在のHTML取得
  2. ClaudeCode で edited.html を生成
  3. python blog_agent.py apply-edit "投稿タイトル" --file edited.html

【その他】
  python blog_agent.py setup --secrets client_secrets.json  # 初回セットアップ
  python blog_agent.py list                                   # 投稿一覧
  python blog_agent.py upload-image --file image.jpg         # 画像アップロード
        """,
    )
    subparsers = parser.add_subparsers(dest="command")

    p_setup = subparsers.add_parser("setup", help="初回セットアップ（認証情報の暗号化保存）")
    p_setup.add_argument("--secrets", required=True, metavar="PATH", help="client_secrets.json のパス")

    subparsers.add_parser("list", help="公開済み投稿一覧を表示")
    subparsers.add_parser("list-drafts", help="下書き一覧を表示")

    p_extract = subparsers.add_parser("extract", help="[下書きStep1] 資料からテキストを抽出")
    p_extract.add_argument("file", help="イベント資料ファイル（.pdf / .docx / .pptx）")

    p_post = subparsers.add_parser("post-draft", help="[下書きStep3] HTMLファイルをBloggerに下書き保存")
    p_post.add_argument("--title", required=True, help="記事タイトル")
    p_post.add_argument("--file", required=True, metavar="HTML_FILE", help="HTMLファイルのパス")

    p_show = subparsers.add_parser("show", help="[編集Step1] 既存投稿のHTMLをファイルに保存")
    p_show.add_argument("title", help="投稿タイトル（部分一致）")

    p_apply = subparsers.add_parser("apply-edit", help="[編集Step3] 修正済みHTMLをBloggerに反映")
    p_apply.add_argument("title", help="投稿タイトル（部分一致）")
    p_apply.add_argument("--file", required=True, metavar="HTML_FILE", help="修正済みHTMLファイルのパス")

    p_upload = subparsers.add_parser("upload-image", help="画像をBloggerにアップロードしてURLを取得")
    p_upload.add_argument("--file", required=True, metavar="IMAGE_FILE", help="画像ファイルのパス")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "setup": cmd_setup,
        "list": cmd_list,
        "list-drafts": cmd_list_drafts,
        "extract": cmd_extract,
        "post-draft": cmd_post_draft,
        "show": cmd_show,
        "apply-edit": cmd_apply_edit,
        "upload-image": cmd_upload_image,
    }

    try:
        commands[args.command](args)
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中断しました。")
        sys.exit(0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
