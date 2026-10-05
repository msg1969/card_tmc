"""公開前チェックと配信ファイルの境界を、隔離した一時フォルダで検証する。"""

from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from check_site import PUBLIC_FILES

ROOT = Path(__file__).resolve().parent.parent


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        for name in PUBLIC_FILES:
            shutil.copyfile(ROOT / name, self.root / name)
        for name in ("build_site.py", "check_site.py"):
            shutil.copyfile(ROOT / "scripts" / name, self.root / "scripts" / name)

    def build(self):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "build_site.py")],
            capture_output=True, text=True,
        )

    def test_only_allowed_files_are_published_and_stale_files_are_removed(self):
        (self.root / ".env").write_text("PRIVATE_TEST_DATA")
        (self.root / "notes.txt").write_text("PRIVATE_TEST_DATA")
        (self.root / "_site").mkdir()
        (self.root / "_site" / "stale.txt").write_text("OLD_TEST_DATA")
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in (self.root / "_site").iterdir()}, set(PUBLIC_FILES))
        for name in PUBLIC_FILES:
            self.assertEqual((self.root / "_site" / name).read_bytes(), (self.root / name).read_bytes())

    def test_unsafe_html_does_not_replace_existing_output(self):
        original = (self.root / "index.html").read_text()
        changes = {
            "script": original.replace("</body>", "<script>alert(1)</script></body>"),
            "handler": original.replace('<img src=', '<img onerror="alert(1)" src=', 1),
            "remote_image": original.replace('src="IMG_9375.png"', 'src="https://example.invalid/photo.png"'),
            "weaker_csp": original.replace("script-src 'none'", "script-src 'self'"),
            "link_without_protection": original.replace('rel="noopener noreferrer"', 'rel="noopener"', 1),
            "javascript_link": original.replace('href="https://x.com/TMC2020"', 'href="javascript:alert(1)"'),
            "redirect": original.replace("</head>", '<meta http-equiv="refresh" content="0;url=https://example.invalid"></head>'),
        }
        (self.root / "_site").mkdir()
        keep = self.root / "_site" / "index.html"
        keep.write_text("PREVIOUS_RELEASE")
        for name, content in changes.items():
            with self.subTest(name=name):
                (self.root / "index.html").write_text(content)
                self.assertNotEqual(self.build().returncode, 0)
                self.assertEqual(keep.read_text(), "PREVIOUS_RELEASE")

    def test_css_resource_loading_is_rejected(self):
        css = self.root / "style.css"
        css.write_text(css.read_text() + '\n@import "https://example.invalid/style.css";')
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse((self.root / "_site").exists())

    def test_image_metadata_is_rejected(self):
        image = self.root / "IMG_9375.png"
        raw = image.read_bytes()
        data = b"tEXt" + b"Comment\x00PRIVATE_TEST_DATA"
        chunk = struct.pack(">I", len(data) - 4) + data + struct.pack(">I", zlib.crc32(data))
        image.write_bytes(raw[:-12] + chunk + raw[-12:])
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse((self.root / "_site").exists())

    def test_symlinks_cannot_publish_or_delete_outside_files(self):
        protected = self.root / "protected"
        protected.mkdir()
        keep = protected / "keep.txt"
        keep.write_text("PRIVATE_TEST_DATA")
        output = self.root / "_site"
        output.symlink_to(protected, target_is_directory=True)
        self.assertNotEqual(self.build().returncode, 0)
        self.assertEqual(keep.read_text(), "PRIVATE_TEST_DATA")
        output.unlink()
        (self.root / "index.html").unlink()
        (self.root / "index.html").symlink_to(keep)
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
