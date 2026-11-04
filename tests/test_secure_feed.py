"""Host-side tests (CPython). Run: python3 -m unittest discover -s tests"""
import http.server, json, os, ssl, subprocess, sys, tempfile, threading, time, types, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ut = types.ModuleType("utime")
ut.mktime = lambda t: time.mktime(t[:6] + (0, 0, 0))
sys.modules["utime"] = ut
import api, secure_http  # noqa: E402

TOKEN = "uhm_feed_secret"
BODY = {"generated_at": "2026-03-01T08:12:54Z", "people": [
    {"name": "A", "location": {"floor_name": "F1", "zone_name": "Z"}, "last_seen_at": "2026-03-01T08:12:00Z"},
    {"name": "Old", "location": {"floor_name": "F1", "zone_name": "Z"}, "last_seen_at": "2026-03-01T07:00:00Z"},
    {"name": "Away", "location": None}]}


class H(http.server.BaseHTTPRequestHandler):
    mode = "ok"
    seen = []

    def do_GET(self):
        H.seen.append(self.headers.get("Authorization"))
        if H.mode == "redirect":
            self.send_response(302); self.send_header("Location", "http://evil/"); self.end_headers(); return
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"error":"Sign-in required"}'); return
        body = b"<html>portal</html>" if H.mode == "portal" else json.dumps(BODY).encode()
        if H.mode == "429":
            self.send_response(429); self.send_header("Retry-After", "120"); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass


def serve(tls=None):
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    if tls:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(*tls)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = tempfile.mkdtemp()
        cls.crt, key = d + "/c.pem", d + "/k.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cls.crt,
                        "-days", "2", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"],
                       check=True, capture_output=True)
        cls.ca = open(cls.crt, "rb").read()
        cls.srv, cls.port = serve((cls.crt, key))
        cls.plain, cls.pport = serve()

    def setUp(self):
        H.mode = "ok"; H.seen.clear()

    def url(self): return "https://localhost:%d/api/presence/current" % self.port

    def test_ok_marks_stale_and_away(self):
        people, err = api.fetch_presence(self.url(), 300, TOKEN, self.ca)
        self.assertIsNone(err)
        self.assertEqual([(p["name"], p["away"]) for p in people], [("A", False), ("Old", True), ("Away", True)])
        self.assertEqual(people[1]["seen"], "07:00")
        self.assertEqual(people[1]["age_s"], 4374)
        self.assertEqual(api._ascii("Zen\u2019s Room"), "Zen's Room")

    def test_bad_token_is_auth_not_nobody_home(self):
        people, err = api.fetch_presence(self.url(), 300, "wrong", self.ca)
        self.assertIsNone(people); self.assertEqual(err.kind, "auth"); self.assertNotIn("wrong", str(err))

    def test_rate_limit(self):
        H.mode = "429"
        _, err = api.fetch_presence(self.url(), 300, TOKEN, self.ca)
        self.assertEqual((err.kind, err.retry_after), ("rate", 120))

    def test_non_feed_200_is_error(self):
        H.mode = "portal"
        people, err = api.fetch_presence(self.url(), 300, TOKEN, self.ca)
        self.assertIsNone(people); self.assertEqual(err.kind, "parse")

    def test_redirect_not_followed_and_token_not_resent(self):
        H.mode = "redirect"
        _, err = api.fetch_presence(self.url(), 300, TOKEN, self.ca)
        self.assertEqual(err.kind, "http"); self.assertEqual(len(H.seen), 1)

    def test_wrong_ca_fails_closed_and_sends_no_token(self):
        other = tempfile.mkdtemp()
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", other + "/k", "-out", other + "/c",
                        "-days", "2", "-subj", "/CN=other"], check=True, capture_output=True)
        _, err = api.fetch_presence(self.url(), 300, TOKEN, open(other + "/c", "rb").read())
        self.assertEqual(err.kind, "net"); self.assertEqual(H.seen, [])

    def test_refuses_http_and_unverified_and_url_token(self):
        for url, ca in [("http://localhost:%d/x" % self.pport, None),
                        (self.url(), None),
                        (self.url() + "?token=" + TOKEN, self.ca)]:
            _, err = api.fetch_presence(url, 300, TOKEN, ca)
            self.assertEqual(err.kind, "net"); self.assertNotIn(TOKEN, str(err))
        self.assertEqual(H.seen, [])


if __name__ == "__main__":
    unittest.main()
