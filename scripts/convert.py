#!/usr/bin/env python3
"""DocMark → Markdown 转换脚本（对齐后端 v2 接口）。

接口契约（与 app.py / API 文档一致）：
  POST {BASE}/convert        multipart form，file 字段上传本地文件
  POST {BASE}/convert/url    JSON body {"url": "http(s)://..."} 远程文件
  鉴权：Authorization: Bearer <API-Key>（亦兼容 X-API-Key）
  支持：.pdf .docx/.doc .pptx/.ppt .xlsx/.xls 及图片 .jpg/.jpeg/.png/.bmp/.webp
  （旧版 Office 扩展名由服务端自动按新格式处理）

仅用 Python 标准库。任何能执行 Python 的 Agent / Skill 环境都可用。
"""
import argparse
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("DOCMARK_BASE", "https://note.prowyg.com").rstrip("/")
MAX_UPLOAD_MB = 50  # 服务端默认上限，仅用于本地上传前提醒（非强制）

SUPPORTED = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".jpg", ".jpeg", ".png", ".bmp", ".webp",
}


class ApiError(Exception):
    def __init__(self, code, message):
        super().__init__(f"HTTP {code}: {message}")
        self.code = code
        self.message = message


def _headers(key: str) -> dict:
    return {"Authorization": "Bearer " + key}


def _read(resp) -> str:
    return resp.read().decode("utf-8")


def _request(req, timeout: int) -> str:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _read(resp)
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode("utf-8")
        except Exception:
            pass
        # 服务端错误通常是 JSON {"detail": "..."}
        detail = raw
        if raw.startswith("{"):
            try:
                detail = json.loads(raw).get("detail") or detail
            except Exception:
                pass
        hint = ""
        if e.code == 402:
            hint = "（积分不足，请到官网 https://www.prowyg.com 充值后重试）"
        elif e.code == 401:
            hint = "（API-Key 无效或已失效，请到官网 https://www.prowyg.com 重新获取）"
        elif e.code == 413:
            hint = "（文件超过服务端上传大小上限，请压缩或换用 URL）"
        raise ApiError(e.code, f"{detail}{hint}")
    except urllib.error.URLError as e:
        raise ApiError(0, f"网络错误，无法连接服务：{e.reason}")


def convert_file(base: str, key: str, path: str, timeout: int = 180) -> str:
    if not os.path.isfile(path):
        raise ApiError(0, f"文件不存在：{path}")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise ApiError(0, f"文件 {size_mb:.1f}MB 可能超过服务端 {MAX_UPLOAD_MB}MB 上限")
    ext = os.path.splitext(path)[1].lower()
    if ext and ext not in SUPPORTED:
        print(f"[warn] 扩展名 {ext} 不在常见支持列表，仍会尝试；支持：{sorted(SUPPORTED)}",
              file=sys.stderr)

    boundary = "----docmark" + os.urandom(8).hex()
    filename = os.path.basename(path)
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        payload = f.read()
    body = io.BytesIO()
    body.write(("--%s\r\n" % boundary).encode("utf-8"))
    body.write(('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode("utf-8"))
    body.write(("Content-Type: %s\r\n\r\n" % ctype).encode("utf-8"))
    body.write(payload)
    body.write(("\r\n--%s--\r\n" % boundary).encode("utf-8"))

    req = urllib.request.Request(
        base + "/convert",
        data=body.getvalue(),
        headers={**_headers(key), "Content-Type": "multipart/form-data; boundary=" + boundary},
        method="POST",
    )
    return _request(req, timeout)


def convert_url(base: str, key: str, url: str, timeout: int = 180) -> str:
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ApiError(0, f"url 仅支持 http/https：{url}")
    data = json.dumps({"url": url}).encode("utf-8")
    req = urllib.request.Request(
        base + "/convert/url",
        data=data,
        headers={**_headers(key), "Content-Type": "application/json"},
        method="POST",
    )
    return _request(req, timeout)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="DocMark：把 PDF/Word/PPT/Excel 或图片转成干净 Markdown（支持本地文件与远程 URL）"
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="本地文件路径")
    src.add_argument("--url", help="远程 http(s) 文件地址")
    ap.add_argument("-k", "--key", help="API-Key；或设置环境变量 DOCMARK_API_KEY")
    ap.add_argument("-b", "--base", default=DEFAULT_BASE,
                    help="API 服务地址（默认 DOCMARK_BASE 或 https://note.prowyg.com）")
    ap.add_argument("-t", "--timeout", type=int, default=180, help="请求超时秒数（默认 180）")
    ap.add_argument("-o", "--out", help="输出到文件；缺省打印到 stdout")
    args = ap.parse_args(argv)

    key = (args.key or os.environ.get("DOCMARK_API_KEY", "")).strip()
    if not key:
        print("Missing API key. Get one at https://www.prowyg.com "
              "(register / create key), then pass --key or set DOCMARK_API_KEY.",
              file=sys.stderr)
        return 2
    base = args.base.rstrip("/")

    try:
        text = convert_url(base, key, args.url, args.timeout) if args.url \
            else convert_file(base, key, args.file, args.timeout)
    except ApiError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3 if e.code else 4
    except Exception as e:  # noqa: BLE001
        print(f"error: unexpected {type(e).__name__}: {e}", file=sys.stderr)
        return 4

    if args.out:
        d = os.path.dirname(os.path.abspath(args.out))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("saved:", args.out, file=sys.stderr)
    else:
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
