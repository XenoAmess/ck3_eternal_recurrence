#!/usr/bin/env python3
"""Configure and verify repository-local Git identity and SSH transport."""

from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from git_operator_common import git_path, resolve_proxy_uri, resolve_transport
from invoke_git_operator import invoke


def _git(
    repository: Path,
    arguments: list[str],
    *,
    capture: bool = False,
    allow_missing: bool = False,
) -> str | None:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository}",
            "-C",
            str(repository),
            *arguments,
        ],
        check=False,
        capture_output=capture or allow_missing,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if allow_missing and completed.returncode == 1:
        return None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"git {' '.join(arguments)} failed for {repository}: {detail}"
        )
    return completed.stdout if capture or allow_missing else ""


def _config(repository: Path, key: str) -> str | None:
    value = _git(
        repository,
        ["config", "--local", "--get", key],
        capture=True,
        allow_missing=True,
    )
    return value.splitlines()[0].strip() if value and value.splitlines() else None


def _set_config(repository: Path, key: str, value: str) -> None:
    _git(repository, ["config", "--local", key, value])


def _identity() -> tuple[str, str]:
    name = getpass.getuser()
    if os.name != "nt":
        return name, "not-windows"
    completed = subprocess.run(
        ["whoami.exe", "/user", "/fo", "csv", "/nh"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return name, "unavailable"
    rows = list(csv.reader(completed.stdout.splitlines()))
    sid = rows[0][1] if rows and len(rows[0]) >= 2 else "unavailable"
    return name, sid


def _ssh_command(key: Path) -> str:
    ssh = shutil.which("ssh.exe") or shutil.which("ssh")
    if ssh is None:
        raise RuntimeError("OpenSSH client is unavailable")
    if not key.is_file():
        raise RuntimeError(f"repository SSH key is unavailable: {key}")
    values = [
        git_path(Path(ssh).resolve()),
        "-i",
        git_path(key.resolve()),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
    ]
    return subprocess.list2cmdline(values) if os.name == "nt" else shlex.join(values)


def _add_global_safe_directory(repository: Path) -> None:
    completed = subprocess.run(
        ["git", "config", "--global", "--get-all", "safe.directory"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError("Unable to read the current operator's global Git configuration")
    normalized = git_path(repository)
    if normalized not in completed.stdout.splitlines():
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", normalized],
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-repository", type=Path)
    parser.add_argument("--open-kaishek-repository", type=Path)
    parser.add_argument("--promo-repository", type=Path)
    parser.add_argument("--auth-root", type=Path)
    parser.add_argument("--git-user-name")
    parser.add_argument("--git-user-email")
    parser.add_argument("--ssh-transport", choices=("direct", "https-proxy"))
    parser.add_argument("--https-proxy")
    parser.add_argument("--connect-command")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--verify-push-dry-run", action="store_true")
    parser.add_argument("--skip-global-safe-directory", action="store_true")
    args = parser.parse_args()
    main_repository = (
        args.main_repository.resolve()
        if args.main_repository
        else Path(__file__).resolve().parents[1]
    )
    open_kaishek = args.open_kaishek_repository or (
        Path(os.environ["XAR_OPEN_KAISHEK_REPOSITORY"])
        if os.environ.get("XAR_OPEN_KAISHEK_REPOSITORY")
        else None
    )
    promo = args.promo_repository or (
        Path(os.environ["XAR_PROMO_TOOLCHAIN_REPOSITORY"])
        if os.environ.get("XAR_PROMO_TOOLCHAIN_REPOSITORY")
        else None
    )
    repositories = [
        ("ck3_eternal_recurrence", main_repository, "master", "ck3_eternal_recurrence_ed25519")
    ]
    if open_kaishek:
        repositories.append(("open_kaishek", open_kaishek.resolve(), "main", "open_kaishek_ed25519"))
    if promo:
        repositories.append(("xar_promo_toolchain", promo.resolve(), "main", "xar_promo_toolchain_ed25519"))
    auth_root = args.auth_root or (
        Path(os.environ["XAR_SHARED_GIT_AUTH_ROOT"])
        if os.environ.get("XAR_SHARED_GIT_AUTH_ROOT")
        else main_repository.parent / f"{main_repository.name}_shared_git_auth"
    )
    windows_name, windows_sid = _identity()
    results = []
    try:
        for product, repository, remote_branch, key_name in repositories:
            if not repository.is_dir():
                raise RuntimeError(f"repository is unavailable: {repository}")
            configured_transport = _config(repository, "xar.sshTransport")
            transport = resolve_transport(
                args.ssh_transport,
                os.environ.get("XAR_GIT_SSH_TRANSPORT"),
                configured_transport,
            )
            proxy = None
            if transport == "https-proxy":
                proxy = resolve_proxy_uri(
                    args.https_proxy,
                    os.environ.get("XAR_GIT_HTTPS_PROXY") or os.environ.get("HTTPS_PROXY"),
                    _config(repository, "xar.httpsProxy"),
                )
            user_name = args.git_user_name or os.environ.get("XAR_GIT_USER_NAME") or _config(repository, "user.name")
            user_email = args.git_user_email or os.environ.get("XAR_GIT_USER_EMAIL") or _config(repository, "user.email")
            if not args.verify_only:
                if not user_name or not user_email:
                    raise RuntimeError("Git identity is unavailable")
                _set_config(repository, "user.name", user_name)
                _set_config(repository, "user.email", user_email)
                _set_config(repository, "core.sshCommand", _ssh_command(auth_root / key_name))
                _set_config(repository, "pull.rebase", "true")
                _set_config(repository, "xar.sshTransport", transport)
                if args.https_proxy and proxy:
                    _set_config(repository, "xar.httpsProxy", proxy)
                if args.connect_command:
                    _set_config(repository, "xar.connectCommand", str(Path(args.connect_command).resolve()))
                if not args.skip_global_safe_directory:
                    _add_global_safe_directory(repository)
            status = _git(repository, ["status", "--short", "--branch", "--untracked-files=no"], capture=True)
            remote = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("invoke_git_operator.py")),
                    "--repository",
                    str(repository),
                    "--ssh-transport",
                    transport,
                    *(["--https-proxy", proxy] if proxy else []),
                    *(["--connect-command", args.connect_command] if args.connect_command else []),
                    "ls-remote",
                    "--exit-code",
                    "origin",
                    f"refs/heads/{remote_branch}",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout
            local_head = (_git(repository, ["rev-parse", "HEAD"], capture=True) or "").strip()
            remote_head = remote.split()[0]
            synchronized = local_head == remote_head
            push_dry_run = "not-requested"
            if args.verify_push_dry_run:
                if synchronized:
                    code = invoke(
                        repository,
                        ["push", "--dry-run", "origin", f"HEAD:{remote_branch}"],
                        ssh_transport=transport,
                        https_proxy=proxy,
                        connect_command=args.connect_command,
                    )
                    if code != 0:
                        raise RuntimeError("Git push dry-run failed")
                    push_dry_run = "ok"
                else:
                    push_dry_run = "skipped-remote-ahead"
            results.append(
                {
                    "repository": product,
                    "path": str(repository),
                    "windows_identity": windows_name,
                    "windows_sid": windows_sid,
                    "status_ok": True,
                    "ls_remote_ok": True,
                    "local_head": local_head,
                    "remote_head": remote_head,
                    "remote_branch": remote_branch,
                    "ssh_transport": transport,
                    "synchronized": synchronized,
                    "push_dry_run": push_dry_run,
                    "status": status,
                }
            )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
