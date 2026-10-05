import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src" / "main.py"


def run(command, a: bytes, b: bytes):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "a").write_bytes(a)
        (p / "b").write_bytes(b)
        return subprocess.run(
            [sys.executable, str(MAIN), command, str(p / "a"), str(p / "b")],
            capture_output=True,
        )


class SolutionTests(unittest.TestCase):
    def test_identical(self):
        r = run("lines", b"a\r\nb\r\n", b"a\r\nb\r\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b" a\r\n b\r\n")

    def test_replace_delete_first(self):
        r = run("lines", b"a\nb\nc\n", b"a\nx\nc\n")
        self.assertEqual(r.stdout, b" a\n-b\n+x\n c\n")

    def test_empty(self):
        r = run("lines", b"", b"")
        self.assertEqual(r.stdout, b"")

    def test_raw_cr_preserved(self):
        r = run("lines", b"a\r\n", b"b\r\n")
        self.assertEqual(r.stdout, b"-a\r\n+b\r\n")

    def test_highlight(self):
        r = run("highlight", b"server:\nport = 8000\n", b"server:\nport = 8080\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"? ", r.stdout)

    def test_unicode_codepoints(self):
        r = run("highlight", "hi 😀\n".encode(), "hi 😃\n".encode())
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"? 3-4 | 3-4\n", r.stdout)

    def test_unpaired_insert(self):
        r = run("highlight", b"a = 1\nb = 2\n", b"a = 10\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"? . | 5-6\n", r.stdout)


if __name__ == "__main__":
    unittest.main()
