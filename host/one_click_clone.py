#!/usr/bin/env python3
"""Chrome native messaging host：把仓库页面 URL 交给本机 git 克隆，再用编辑器打开。

Chrome 用系统 python（3.9）启动本文件，代码需保持 3.9 兼容。
"""
import json
import os
import re
import struct
import subprocess
import sys
from urllib.parse import unquote, urlsplit

REF_MARKERS = ("tree", "blob")
EXTRA_PATH = "/opt/homebrew/bin:/usr/local/bin"
REMOTE_PROGRESS = re.compile(r"remote: (Enumerating|Counting|Compressing|Total) ")


def parse_page_url(page_url):
    """返回 (仓库地址, 目录名, 分支候选路径段)。github.com 取前两段，其它域名按 GitLab 取 /-/ 之前的路径。"""
    url = urlsplit(page_url)
    if url.scheme not in ("http", "https"):
        raise ValueError(f"不是仓库页面：{page_url}")
    parts = [unquote(p) for p in url.path.split("/") if p]
    if url.hostname == "github.com":
        repo_parts, rest = parts[:2], parts[2:]
    elif "-" in parts:
        index = parts.index("-")
        repo_parts, rest = parts[:index], parts[index + 1 :]
    else:
        repo_parts, rest = parts, []
    if len(repo_parts) < 2:
        raise ValueError(f"不是仓库页面：{page_url}")
    repo_parts[-1] = repo_parts[-1].removesuffix(".git")
    ref_parts = rest[1:] if rest and rest[0] in REF_MARKERS else []
    return f"{url.scheme}://{url.netloc}/{'/'.join(repo_parts)}.git", repo_parts[-1], ref_parts


def resolve_ref(ref_parts, list_refs):
    """URL 里分支名和文件路径都用 / 分隔，取远程实际存在的最长前缀作为分支或标签。"""
    if len(ref_parts) <= 1:
        return ref_parts[0] if ref_parts else None
    refs = list_refs()
    for end in range(len(ref_parts), 0, -1):
        candidate = "/".join(ref_parts[:end])
        if candidate in refs:
            return candidate
    raise ValueError(f"远程没有这个分支或标签：{'/'.join(ref_parts)}")


def normalize_repo(url):
    scp = re.match(r"^[\w.-]+@([^:/]+):(.+)$", url)
    if scp:
        host, path = scp.groups()
    else:
        parsed = urlsplit(url)
        host, path = parsed.hostname, parsed.path
    return f"{host}/{path.strip('/').removesuffix('.git')}".lower()


def same_repo(a, b):
    return normalize_repo(a) == normalize_repo(b)


def run_git(args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, env=git_env())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def git_env():
    # 固定英文输出，进度和报错前缀才能稳定匹配；禁止 git 交互式询问账号
    return {**os.environ, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"}


def list_remote_refs(repo_url):
    lines = run_git(["ls-remote", "--heads", "--tags", repo_url]).splitlines()
    return {re.sub(r"^refs/(heads|tags)/|\^\{\}$", "", line.split("\t")[1]) for line in lines}


def clone(repo_url, ref, target, send):
    branch_args = ["--branch", ref] if ref else []
    proc = subprocess.Popen(
        ["git", "clone", "--progress", *branch_args, repo_url, target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=git_env(),
    )
    log, last_percent = b"", None
    chunk = proc.stderr.read1(4096)
    while chunk:
        log += chunk
        percents = re.findall(rb"Receiving objects:\s+(\d+)%", chunk)
        if percents and percents[-1] != last_percent:
            last_percent = percents[-1]
            send({"type": "progress", "percent": int(last_percent)})
        chunk = proc.stderr.read1(4096)
    if proc.wait() != 0:
        lines = re.split(r"[\r\n]+", log.decode(errors="replace"))
        errors = [l for l in lines if l.startswith(("fatal:", "error:", "remote:")) and not REMOTE_PROGRESS.match(l)]
        raise RuntimeError("\n".join(errors) or log.decode())


def handle(request, send):
    repo_url, name, ref_parts = parse_page_url(request["pageUrl"])
    target = os.path.join(os.path.expanduser(request["root"]), name)
    existed = os.path.exists(target)
    if existed:
        origin = run_git(["-C", target, "remote", "get-url", "origin"]).strip()
        if not same_repo(origin, repo_url):
            raise RuntimeError(f"目录已存在但不是这个仓库：{target}（origin: {origin}）")
    else:
        clone(repo_url, resolve_ref(ref_parts, lambda: list_remote_refs(repo_url)), target, send)
    if request.get("editor"):
        subprocess.run(["open", "-a", request["editor"], target], check=True, capture_output=True)
    send({"type": "done", "dir": target, "existed": existed})


def read_message():
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        sys.exit(0)
    return json.loads(sys.stdin.buffer.read(struct.unpack("=I", header)[0]))


def send_message(message):
    data = json.dumps(message, ensure_ascii=False).encode()
    sys.stdout.buffer.write(struct.pack("=I", len(data)) + data)
    sys.stdout.buffer.flush()


def main():
    # Chrome 从 Dock 启动时 PATH 只有系统目录，补上 Homebrew 让 git 与终端一致
    os.environ["PATH"] = f"{EXTRA_PATH}:{os.environ.get('PATH', '')}"
    request = read_message()
    try:
        handle(request, send_message)
    except subprocess.CalledProcessError as e:
        send_message({"type": "error", "error": f"打开编辑器失败：{e.stderr.decode().strip()}"})
    except Exception as e:
        send_message({"type": "error", "error": str(e)})


if __name__ == "__main__":
    main()
