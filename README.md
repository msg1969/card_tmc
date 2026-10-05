# とやめんの自己紹介カード

生成AIセキュア開発講座（#AIセキュア1st）向けの静的な自己紹介カードです。
HTML・CSS・ローカル画像だけで表示し、JavaScript・外部フォント・解析タグは使いません。
ベースカラーはミッドナイトネイビー（`#10151D`）、INTJ-Aのバッジは紫です。

## 手元で確認

```sh
python3 scripts/build_site.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

ブラウザで <http://127.0.0.1:8000/> を開きます。終了はターミナルで Ctrl+C。
`index.html`、`style.css`、画像を編集したら、ビルドを再実行してブラウザを更新します。
HTMLファイルを直接開くと、ブラウザによってCSPによる表示制限が異なるため、HTTPで確認します。

## GitHub Pagesへの反映

**このカードでは、既存のGitHub Pagesを継続し、チェック付きのGitHub Actionsで配信する方法を推奨します。**
公開プロフィールと外部リンクだけの小さな静的サイトなので、サーバーやデータベース、追加の認証用Secretは不要です。

公開先: <https://msg1969.github.io/card_tmc/>

1. GitHubリポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に変更します。
2. **Enforce HTTPS** が有効なことを確認します。
3. **Settings → Environments → github-pages** の配信元ブランチを `main` に限定します。ワークフローにも `main` 以外は公開しない条件を入れています。
4. GitHubアカウントをパスキーまたは2段階認証で保護し、リポジトリの書き込み権限は必要な人だけにします。
5. 差分と公開するプロフィール内容を確認し、必要な変更だけをコミットして `main` にpushします。
6. **Actions → Publish introduction card** のテスト・公開前チェック・配信がすべて完了した後、公開URLで受講歴、ハッシュタグ、画像、外部リンクを確認します。

公開前のテストはローカルでも実行できます。

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build_site.py
```

公開前チェックは、スクリプト・イベント属性・フォームなどの追加、CSPの変更、外部リソース読み込み、
外部リンク保護の欠落、PNGへのEXIF・テキスト情報の混入を検出すると失敗します。
失敗した場合は `_site` を更新せず、Actionsも配信に進みません。
これはこのカードの構成を保つためのチェックであり、秘密情報を完全に検出するスキャナーや、任意のHTMLを安全に変換する仕組みではありません。

公開ワークフローは `_site` の5ファイルだけを配信します。リポジトリ全体や作業フォルダをアップロードしないでください。
既存の「main / ルートから公開」の設定のままでは、この5ファイル限定の配信には切り替わりません。
初回は手順1の設定変更が必要です。追加のAPIキーや独自Secretは不要です。

この変更を手元に用意しただけでは公開サイトは更新されません。
2026-10-05に公開方式をGitHub Actionsへ切り替えました。リポジトリは公開、HTTPSは有効です。
`github-pages` 環境の配信元は `main` ブランチに限定しています。

公開後はHTTPからHTTPSへの転送、表示、QRコードからの遷移を確認し、`/.env`・`/.git/config`などが取得できないことも確認します。
GitHub PagesはプロジェクトURLなので、チェックするパスは `/card_tmc/.env` のように公開URLを基準にします。
問題があれば、直前の正常な変更へrevertしたコミットを `main` にpushし、同じチェックと配信を通して戻します。

## 公開時の保護と範囲

- CSPでスクリプト、フォーム送信、埋め込みオブジェクトを禁止し、CSS・画像は同じ配信元だけを許可。
- 外部リンクはHTTPSに統一し、`noopener noreferrer` と `no-referrer` を指定。
- 猫のPNG画像からEXIF・テキストメタデータを除去。写真を差し替えた場合も、位置情報などを除去してから公開。
- 公式GitHub ActionsはコミットSHAで固定。公開権限はデプロイのジョブに限定。
- `.env`、鍵ファイル、作業用画像をGit管理対象から除外。公開リポジトリでは、配信対象外のファイルや過去の履歴も第三者が読めるため、秘密情報はコミットしない。

HTML内のCSPはHTTPレスポンスヘッダーの代わりにすべての制限を設定できるものではありません。
特に `frame-ancestors`（他サイトによる埋め込みの制限）はmetaタグでは無効なので記載していません。
このカードにはログインや入力・更新操作はありません。将来それらを加える場合は、ヘッダー設定とサーバー側の保護も含めて再検討してください。

## HTTPヘッダーによる保護まで行う場合

他サイトからの埋め込み禁止や `X-Content-Type-Options` なども明示的に管理したい場合は、
**Cloudflare Pagesで同じ静的ファイルを配信する案**があります。
Cloudflare Pagesは `_headers` で静的配信のレスポンスヘッダーを設定できます。
移行する場合は、公開前チェックを通した `_site` に次の `_headers` を加え、ビルド出力として指定します。

```text
/*
  Content-Security-Policy: default-src 'none'; script-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-ancestors 'none'
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: no-referrer
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
```

GitHub Pagesへ `_headers` を置くだけでは、この設定は適用されません。
Cloudflare案を選ぶ場合は、公開先URLに合わせてOGP・共有画像のURLを更新し、
Git連携またはアップロードの公開経路と権限を設定したうえで、実際のHTTPレスポンスでヘッダーの有効化を確認します。
この案のアカウント作成・接続・デプロイは行っていません。

根拠: [MDN: CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy)、
[MDN: frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors)、
[GitHub: HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)、
[GitHub: Pagesワークフロー](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、
[Cloudflare Pages: Headers](https://developers.cloudflare.com/pages/configuration/headers/)。

## ファイル

- `index.html`: 自己紹介、受講歴、外部リンク、共有用メタ情報
- `style.css`: 配色・余白・PC／スマートフォンの配置
- `IMG_9375.png`: 猫のアバター
- `qrcode_x.com.png`: XプロフィールのQRコード
- `ogp.png`: SNS共有用プレビュー（1200 × 630）
- `scripts/build_site.py`: 公開する5ファイルの取り出し
- `scripts/check_site.py`: 公開前の構成・メタデータチェック
- `scripts/test_publication.py`: 拒否すべき変更・公開対象の限定・既存出力の保持を検証するテスト
- `.github/workflows/pages.yml`: GitHub Pagesへの配信
