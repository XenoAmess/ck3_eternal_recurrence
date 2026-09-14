"""Shared policy and transport primitives for the Python Git operator."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import ssl
from urllib.parse import urlparse
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener


HOST_KEY = re.compile(
    r"(?:ssh-ed25519|ecdsa-sha2-nistp256|ssh-rsa) [A-Za-z0-9+/]+={0,3}\Z"
)


def git_path(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def assert_git_arguments(arguments: list[str]) -> None:
    if not arguments:
        raise ValueError("A Git subcommand is required")
    subcommand = arguments[0].lower()
    if subcommand == "merge":
        raise ValueError("git merge is forbidden in this project; fetch and rebase instead")
    if subcommand == "pull" and not any(
        value == "--rebase"
        or (
            value.startswith("--rebase=")
            and value not in {"--rebase=false", "--rebase=no"}
        )
        for value in arguments
    ):
        raise ValueError("git pull must include --rebase in this project")
    if subcommand == "push" and any(
        value in {"-f", "--force", "--force-with-lease", "--mirror"}
        or value.startswith("--force=")
        or value.startswith("--force-with-lease=")
        or value.startswith("+")
        for value in arguments
    ):
        raise ValueError("force push is forbidden in this project")


def resolve_transport(
    explicit: str | None,
    environment: str | None,
    configured: str | None,
) -> str:
    selected = next(
        (value for value in (explicit, environment, configured, "direct") if value and value.strip()),
        "direct",
    ).strip().lower()
    if selected not in {"direct", "https-proxy"}:
        raise ValueError(
            f"Unsupported SSH transport {selected!r}; expected direct or https-proxy"
        )
    return selected


def resolve_proxy_uri(
    explicit: str | None,
    environment: str | None,
    configured: str | None,
) -> str:
    selected = next(
        (value for value in (explicit, environment, configured) if value and value.strip()),
        None,
    )
    if selected is None:
        raise ValueError(
            "https-proxy transport requires XAR_GIT_HTTPS_PROXY, HTTPS_PROXY, "
            "--https-proxy, or local xar.httpsProxy"
        )
    parsed = urlparse(selected)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("The HTTPS proxy must be an absolute http:// URI")
    if parsed.username or parsed.password:
        raise ValueError(
            "Proxy credentials are not accepted; use a credential-free local proxy endpoint"
        )
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("The HTTPS proxy URI must contain only scheme, host, and port")
    port = parsed.port or 80
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"http://{host}:{port}"


def resolve_connect_command(explicit: str | None) -> str:
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_file():
            raise ValueError(f"connect command is unavailable: {path}")
        return str(path)
    found = shutil.which("connect.exe") or shutil.which("connect")
    if found:
        return str(Path(found).resolve())
    git = shutil.which("git.exe") or shutil.which("git")
    if git:
        candidate = Path(git).resolve().parents[1] / "mingw64" / "bin" / "connect.exe"
        if candidate.is_file():
            return str(candidate)
    raise ValueError(
        "Git for Windows connect.exe is unavailable; set XAR_GIT_CONNECT_COMMAND "
        "or local xar.connectCommand"
    )


def github_known_host_lines(host_keys: list[str]) -> list[str]:
    if not host_keys:
        raise ValueError("GitHub metadata returned no SSH host keys")
    lines: list[str] = []
    for key in host_keys:
        if HOST_KEY.fullmatch(key) is None:
            raise ValueError("GitHub metadata returned an unsupported SSH host-key record")
        lines.extend((f"[github.com]:443 {key}", f"[ssh.github.com]:443 {key}"))
    return lines


def github_proxy_ssh_config_lines(
    known_hosts_path: str | Path,
    proxy_uri: str,
    connect_command: str | Path,
) -> list[str]:
    for value in (str(known_hosts_path), str(connect_command)):
        if '"' in value or "\r" in value or "\n" in value:
            raise ValueError("SSH transport paths cannot contain quotes or newlines")
    parsed = urlparse(proxy_uri)
    proxy_host = parsed.hostname or ""
    if ":" in proxy_host:
        proxy_host = f"[{proxy_host}]"
    return [
        "Host github.com ssh.github.com",
        "  HostName ssh.github.com",
        "  Port 443",
        "  User git",
        "  BatchMode yes",
        "  IdentitiesOnly yes",
        "  StrictHostKeyChecking yes",
        f'  UserKnownHostsFile "{git_path(known_hosts_path)}"',
        f'  ProxyCommand "{git_path(connect_command)}" -H {proxy_host}:{parsed.port or 80} %h %p',
    ]


def add_ssh_config_argument(base_command: str, config_path: str | Path) -> str:
    value = str(config_path)
    if '"' in value or "\r" in value or "\n" in value:
        raise ValueError("SSH config path cannot contain quotes or newlines")
    return f'{base_command} -F "{git_path(value)}"'


def get_github_ssh_host_keys(output_path: Path, proxy_uri: str) -> list[str]:
    request = Request(
        "https://api.github.com/meta",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "xar-git-operator",
        },
    )
    context = ssl.create_default_context()
    proxy = ProxyHandler({"http": proxy_uri, "https": proxy_uri})
    opener = build_opener(proxy, HTTPSHandler(context=context))
    payload = opener.open(request, timeout=20).read()
    output_path.write_bytes(payload)
    decoded = json.loads(payload.decode("utf-8"))
    keys = decoded.get("ssh_keys")
    if not isinstance(keys, list) or not all(isinstance(value, str) for value in keys):
        raise ValueError("GitHub metadata lacks an ssh_keys list")
    return keys
