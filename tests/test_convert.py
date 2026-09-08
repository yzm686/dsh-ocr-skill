#!/usr/bin/env python3
"""convert.py 自测：用本地假服务验证请求路径/头/表单与 JSON，不需真实 API。

运行：python tests/test_convert.py
"""
import http.server
import json
import os
import sys
import threading
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import convert  # noqa: E402

RECORDS = []


class Handler(http.server.BaseHTTPRequestHandler):
    def _record(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(n) if n else b""
        RECORDS.append({
            "method": self.command,
            "path": self.path,
            "auth": self.headers.get("Authorization"),
            "ctype": self.headers.get("Content-Type"),
            "body": body,
        })
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"# ok\n")

    do_POST = _record
    do_GET = _record

    def log_message(self, *a):  # silence
        pass


def start_server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def main() -> int:
    srv, base = start_server()
    fails = []

    # 1) file → multipart POST /convert + Bearer
    tmp = os.path.join(os.path.dirname(__file__), "sample.pdf")
    open(tmp, "wb").write(b"%PDF-1.4 demo")
    try:
        convert.convert_file(base, "md_test", tmp)
    finally:
        os.remove(tmp)
    r = RECORDS[-1]
    if r["path"] != "/convert" or r["method"] != "POST":
        fails.append("file path/method")
    if r["auth"] != "Bearer md_test":
        fails.append("file auth")
    if 'name="file"' not in r["body"].decode("utf-8", "replace"):
        fails.append("file field")

    # 2) url → JSON POST /convert/url
    convert.convert_url(base, "md_test", "https://example.com/a.pdf")
    r = RECORDS[-1]
    if r["path"] != "/convert/url":
        fails.append("url path")
    try:
        j = json.loads(r["body"].decode("utf-8"))
        if j.get("url") != "https://example.com/a.pdf":
            fails.append("url body")
    except Exception:
        fails.append("url json")

    # 3) 非 http(s) url 拒绝
    try:
        convert.convert_url(base, "md_test", "ftp://x/a.pdf")
        fails.append("url scheme accepted")
    except convert.ApiError:
        pass

    srv.shutdown()
    if fails:
        print("FAIL:", "; ".join(fails))
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
