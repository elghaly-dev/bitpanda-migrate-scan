import hashlib
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bitpanda_migrate_scan as s  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
SECRET = "Zq8Lm2Vx9Rt4Yp7Nc1Bd6Hs3Kw5Jf0Ga"


def hits_for(name):
    return [h for h in s.scan_path(FIX) if h["file"] == name]


class ScannerTests(unittest.TestCase):
    def test_apps_script(self):
        h = hits_for("sample.gs")
        self.assertEqual([(x["line"], x["new"]) for x in h],
                         [(3, ["GET /v1/portfolio"]), (8, ["GET /v1/operations"])])

    def test_home_assistant_yaml(self):
        h = hits_for("ha_config.yaml")
        self.assertEqual([(x["line"], x["new"][0]) for x in h],
                         [(4, "GET /v1/portfolio"), (9, "GET /v1/assets")])

    def test_python_endpoints_and_key(self):
        h = hits_for("sample.py")
        eps = [(x["line"], x.get("new"), x.get("note")) for x in h if x["kind"] == "legacy-endpoint"]
        self.assertEqual(eps[0][0], 3)
        self.assertIn("Legacy base URL", eps[0][2])
        self.assertEqual(eps[1][:2], (7, ["GET /v1/operations"]))
        self.assertIn("no mapping", eps[2][2])
        keys = [x for x in h if x["kind"] == "possible-key"]
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0]["line"], 4)
        self.assertEqual(keys[0]["fingerprint"], hashlib.sha256(SECRET.encode()).hexdigest()[:8])

    def test_clean_file_has_no_hits(self):
        self.assertEqual(hits_for("clean.js"), [])

    def test_dotenv_never_read(self):
        self.assertEqual(hits_for(".env.local"), [])

    def test_secret_never_in_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = s.main([FIX])
        out = buf.getvalue()
        self.assertEqual(rc, 1)
        self.assertNotIn(SECRET, out)
        self.assertNotIn("X-API-KEY", out)
        self.assertIn("sha256:" + hashlib.sha256(SECRET.encode()).hexdigest()[:8], out)
        self.assertIn("Balances and", out)
        self.assertIn("IP allow list", out)

    def test_longest_path_wins(self):
        self.assertEqual(s.lookup("/v1/fiatwallets/transactions?x=1".split("?")[0])[1], ["GET /v1/operations"])
        self.assertEqual(s.lookup("/v1/wallets")[1], ["GET /v1/portfolio"])
        self.assertIsNone(s.lookup("/v1/unknown"))

    def test_new_host_not_flagged(self):
        self.assertEqual(list(s.scan_text("https://api.public.bitpanda.com/v1/portfolio")), [])

    def test_exit_zero_and_missing_path(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(s.main([FIX, "--exit-zero"]), 0)
            self.assertEqual(s.main([FIX + "/nope"]), 2)


if __name__ == "__main__":
    unittest.main()
