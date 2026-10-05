"""公開を許可した5ファイルだけを _site に取り出す（Python標準ライブラリのみ）。"""

from pathlib import Path
import shutil
import tempfile
from check_site import PUBLIC_FILES, check_site

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "_site"


def main():
    # チェックに失敗した場合は、既存の公開用ファイルも更新しない。
    check_site(ROOT)
    # シンボリックリンク経由で別の場所を公開・削除しない。
    for name in PUBLIC_FILES:
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise SystemExit(f"公開ファイルを確認してください: {name}")
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise SystemExit("_site は通常の出力ディレクトリにしてください。")

    with tempfile.TemporaryDirectory(prefix=".build-", dir=ROOT) as temp:
        staging = Path(temp) / "site"
        staging.mkdir()
        for name in PUBLIC_FILES:
            shutil.copyfile(ROOT / name, staging / name)
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        staging.rename(OUTPUT)

    print("公開用ファイルを _site に作成しました:")
    for name in PUBLIC_FILES:
        print(f"  {name}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit(f"公開用ファイルの作成を中止しました: {error}")
