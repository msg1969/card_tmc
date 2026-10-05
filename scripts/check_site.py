"""静的カードの公開前チェック。秘密情報の完全な検出やHTMLの無害化は目的としない。"""

from html.parser import HTMLParser
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit
import zlib

PUBLIC_FILES = (
    "index.html", "style.css", "IMG_9375.png", "qrcode_x.com.png", "ogp.png",
)
POLICY = {
    "default-src": "'none'", "script-src": "'none'", "style-src": "'self'",
    "img-src": "'self'", "base-uri": "'none'", "form-action": "'none'",
    "object-src": "'none'",
}
ALLOWED_TAGS = {
    "html", "head", "meta", "title", "link", "body", "main", "article",
    "header", "footer", "section", "div", "span", "h1", "h2", "h3",
    "p", "br", "ol", "li", "a", "img",
}
ALLOWED_ATTRIBUTES = {
    "lang", "charset", "http-equiv", "content", "name", "property", "rel",
    "href", "type", "class", "id", "src", "alt", "width", "height",
    "target", "role", "aria-label", "aria-labelledby", "aria-hidden", "aria-current",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class CardHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csp_seen = False
        self.referrer_seen = False

    def handle_starttag(self, tag, attributes):
        require(tag in ALLOWED_TAGS, f"許可していないHTML要素: {tag}")
        attrs = dict(attributes)
        require(len(attrs) == len(attributes), "HTML属性が重複しています。")
        require(set(attrs) <= ALLOWED_ATTRIBUTES, f"許可していないHTML属性: {tag}")
        if tag == "meta":
            kind = attrs.get("http-equiv", "").lower()
            require(kind in ("", "content-security-policy"), "不要なhttp-equivがあります。")
            if kind:
                require(not self.csp_seen, "CSPが重複しています。")
                entries = [p.strip().split(maxsplit=1) for p in attrs.get("content", "").split(";") if p.strip()]
                require(all(len(p) == 2 for p in entries), "CSPの書式を確認してください。")
                require(len(entries) == len(POLICY) and dict(entries) == POLICY, "CSPが想定の制限から変更されています。")
                self.csp_seen = True
            if attrs.get("name") == "referrer":
                require(attrs.get("content") == "no-referrer", "Referrer制限を確認してください。")
                self.referrer_seen = True
        if tag in ("link", "img"):
            require(self.csp_seen, "CSPをリソースの読み込みより前に置いてください。")
            resource = attrs.get("href" if tag == "link" else "src")
            allowed = {"style.css"} if attrs.get("rel") == "stylesheet" else set(PUBLIC_FILES[2:])
            require(resource in allowed, "ローカルの公開対象以外のリソースが指定されています。")
            if tag == "link":
                require(attrs.get("rel") in ("stylesheet", "icon"), "不要なリソースリンクがあります。")
            else:
                require(bool(attrs.get("alt")), "画像の代替テキストがありません。")
        if tag == "a":
            url = urlsplit(attrs.get("href", ""))
            require(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password, "外部リンクは認証情報を含まないHTTPS URLにしてください。")
            require({"noopener", "noreferrer"} <= set(attrs.get("rel", "").split()), "外部リンクの保護が不足しています。")
            require("ping" not in attrs, "リンクの追跡送信は使用しません。")


def check_png(path):
    data = path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"PNGではありません: {path.name}")
    offset = 8
    # 色・透過・解像度を保ち、EXIF、テキスト、未知の付加情報は許可しない。
    allowed = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"cHRM", b"gAMA", b"sRGB", b"iCCP", b"sBIT", b"tRNS", b"bKGD", b"pHYs"}
    while offset + 12 <= len(data):
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + size + 12
        require(end <= len(data) and kind in allowed, f"PNGの構造またはメタデータを確認してください: {path.name}")
        checksum = struct.unpack(">I", data[end - 4:end])[0]
        require(zlib.crc32(data[offset + 4:end - 4]) == checksum, f"PNGが破損しています: {path.name}")
        offset = end
        if kind == b"IEND":
            require(size == 0 and offset == len(data), f"PNGに余分なデータがあります: {path.name}")
            return
    raise ValueError(f"PNGが完結していません: {path.name}")


def check_site(root):
    for name in PUBLIC_FILES:
        path = root / name
        require(path.is_file() and not path.is_symlink(), f"公開ファイルを確認してください: {name}")
    parser = CardHTML()
    parser.feed((root / "index.html").read_text(encoding="utf-8"))
    parser.close()
    require(parser.csp_seen and parser.referrer_seen, "CSPまたはReferrer制限がありません。")
    css = (root / "style.css").read_text(encoding="utf-8")
    require(not re.search(r"@import|url\s*\(|image-set\s*\(|\\", css, re.I), "CSSでの追加リソース読み込み・エスケープは使用しません。")
    for name in PUBLIC_FILES[2:]:
        check_png(root / name)
    print("公開前チェックOK: CSP・静的HTML・ローカルリソース・外部リンク保護・PNGメタデータ")


if __name__ == "__main__":
    try:
        check_site(Path(__file__).resolve().parent.parent)
    except (ValueError, OSError) as error:
        raise SystemExit(f"公開前チェックNG: {error}")
