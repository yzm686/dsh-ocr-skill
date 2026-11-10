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
import time
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("DOCMARK_BASE", "https://note.prowyg.com").rstrip("/")
MAX_UPLOAD_MB = 50  # 服务端默认上限，仅用于本地上传前提醒（非强制）

SUPPORTED = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".jpg", ".jpeg", ".png", ".bmp", ".webp",
}

REGISTER_URL = "https://www.prowyg.com"


def fail(msg: str, code: int) -> int:
    """失败信息同时写 stderr 和 stdout。

    只写 stderr 是个坑：智能体调用时常常只捕获 stdout，stderr 被丢掉，
    用户就只看到一个孤零零的退出码，完全不知道要去哪注册 / 充值。
    失败时 stdout 本来就没有 Markdown，不存在污染输出契约的问题。
    """
    print(f"error: {msg}", file=sys.stderr)
    print(f"error: {msg}", file=sys.stdout)
    return code


class ApiError(Exception):
    def __init__(self, code, message):
        super().__init__(f"HTTP {code}: {message}")
        self.code = code
        self.message = message


def _headers(key: str) -> dict:
    return {"Authorization": "Bearer " + key}


def _read(resp) -> str:
    return resp.read().decode("utf-8")


def _request(req, timeout: int):
    """发请求，返回 (status, body)。4xx/5xx 转 ApiError，网络错误转 code=0。"""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _read(resp)
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


def convert_file(base: str, key: str, path: str, timeout: int = 180):
    """上传本地文件，返回 (status, body)。status=202 时 body 是任务 JSON。"""
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


def _task_endpoints(base: str, task_id: str) -> tuple:
    return (f"{base}/convert/tasks/{task_id}", f"{base}/convert/tasks/{task_id}/result")


def poll_task(base: str, key: str, task_id: str, *, interval: float = 3.0,
              timeout: int = 1800, quiet: bool = False) -> str:
    """轮询任务直到终态，返回 Markdown。进度写 stderr，不污染 stdout。"""
    status_url, result_url = _task_endpoints(base, task_id)
    t0 = time.time()
    last = None
    while True:
        req = urllib.request.Request(status_url, headers=_headers(key), method="GET")
        _, body = _request(req, 30)
        try:
            meta = json.loads(body)
        except Exception:
            raise ApiError(0, f"任务状态返回非 JSON：{body[:120]}")
        st = meta.get("status")
        done, total = meta.get("donePages"), meta.get("totalPages")
        cur = (st, done, total)
        if cur != last and not quiet:
            print(f"[task] {time.time() - t0:5.1f}s {st} {done}/{total} 页", file=sys.stderr)
            last = cur
        if st == "succeeded":
            req = urllib.request.Request(result_url, headers=_headers(key), method="GET")
            _, md = _request(req, 120)
            if not quiet:
                print(f"[task] 完成：{meta.get('chars') or len(md)} 字符，"
                      f"耗时 {time.time() - t0:.1f}s", file=sys.stderr)
            return md
        if st == "failed":
            # code=1（非 0）让 main 归为退出码 3「服务端错误」；用 0 会被误判成网络错误 4
            raise ApiError(1, f"任务失败：{meta.get('error')}（服务端已自动退还积分）")
        if time.time() - t0 > timeout:
            raise ApiError(1, f"任务超时（{timeout}s 未完成），可稍后用 --task {task_id} 继续取结果")
        time.sleep(max(0.5, interval))


def convert_url(base: str, key: str, url: str, timeout: int = 180):
    """提交远程 URL，返回 (status, body)。"""
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


class _Parser(argparse.ArgumentParser):
    """参数错误时也带上注册指引。

    argparse 默认只往 stderr 打 usage 就 exit(2)，智能体只看到退出码，
    用户根本不知道要先去注册拿 Key——把参数错误和缺 Key 的引导对齐到同一个出口。
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        raise SystemExit(fail(
            f"参数错误：{message}\n"
            f"       正确用法：--file <本地文件> | --url <http地址> | --task <任务ID>（三选一）\n"
            f"       还没有 API Key？到 {REGISTER_URL} 注册并在控制台创建（新用户送 100 积分）。",
            2,
        ))


def main(argv=None) -> int:
    ap = _Parser(
        description="DocMark：把 PDF/Word/PPT/Excel 或图片转成干净 Markdown（支持本地文件与远程 URL）"
    )
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--file", help="本地文件路径")
    src.add_argument("--url", help="远程 http(s) 文件地址")
    src.add_argument("--task", help="直接查询已存在的任务 ID（大文档转异步时用）")
    ap.add_argument("-k", "--key", help="API-Key；或设置环境变量 DOCMARK_API_KEY")
    ap.add_argument("-b", "--base", default=DEFAULT_BASE,
                    help="API 服务地址（默认 DOCMARK_BASE 或 https://note.prowyg.com）")
    ap.add_argument("-t", "--timeout", type=int, default=180,
                    help="单次请求超时秒数（默认 180；轮询总时长用 --poll-timeout）")
    ap.add_argument("-o", "--out", help="输出到文件；缺省打印到 stdout")
    ap.add_argument("--no-poll", action="store_true",
                    help="大文档转异步时不轮询，直接输出 taskId JSON（稍后用 --task 取）")
    ap.add_argument("--poll-interval", type=float, default=3.0, help="轮询间隔秒（默认 3）")
    ap.add_argument("--poll-timeout", type=int, default=1800,
                    help="轮询总时长上限秒（默认 1800，大文档可调大）")
    ap.add_argument("-q", "--quiet", action="store_true", help="不在 stderr 打印轮询进度")
    args = ap.parse_args(argv)

    if not (args.file or args.url or args.task):
        return fail(
            f"必须指定 --file / --url / --task 三选一。\n"
            f"       还没有 API Key？到 {REGISTER_URL} 注册并在控制台创建（新用户送 100 积分）。",
            2,
        )

    key = (args.key or os.environ.get("DOCMARK_API_KEY", "")).strip()
    if not key:
        return fail(
            "缺少 API Key。请到 {url} 注册并创建 Key（新用户送 100 积分，够跑 100 页），\n"
            "       然后二选一：\n"
            "         1) 设置环境变量： set DOCMARK_API_KEY=md_你的Key\n"
            "         2) 直接传入：     python scripts/convert.py --file 文件.pdf --key md_你的Key\n"
            "       不要臆造或复用他人的 Key。".format(url=REGISTER_URL),
            2,
        )
    base = args.base.rstrip("/")

    try:
        if args.task:
            text = poll_task(base, key, args.task, interval=args.poll_interval,
                             timeout=args.poll_timeout, quiet=args.quiet)
        else:
            status, body = convert_url(base, key, args.url, args.timeout) if args.url \
                else convert_file(base, key, args.file, args.timeout)
            if status == 202:
                # 大文档转异步：服务端已按页扣费，立即返回 taskId
                try:
                    info = json.loads(body)
                except Exception:
                    raise ApiError(0, f"异步任务返回非 JSON：{body[:120]}")
                tid = info.get("taskId")
                if args.no_poll:
                    sys.stdout.write(body if body.endswith("\n") else body + "\n")
                    print(f"[task] 已转异步：taskId={tid}；稍后用 --task {tid} 取结果",
                          file=sys.stderr)
                    return 0
                print(f"[task] 文档较大，已转后台：taskId={tid} "
                      f"{info.get('totalPages')} 页，开始轮询（间隔 {args.poll_interval:g}s）",
                      file=sys.stderr)
                text = poll_task(base, key, tid, interval=args.poll_interval,
                                 timeout=args.poll_timeout, quiet=args.quiet)
            else:
                text = body
    except ApiError as e:
        return fail(str(e), 3 if e.code else 4)
    except Exception as e:  # noqa: BLE001
        return fail(f"unexpected {type(e).__name__}: {e}", 4)

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
