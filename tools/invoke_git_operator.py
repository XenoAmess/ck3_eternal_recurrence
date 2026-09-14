#!/usr/bin/env python3
"""Run Git with repository-local identity and fail-closed history policy."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from git_operator_common import (
    add_ssh_config_argument,
    assert_git_arguments,
    get_github_ssh_host_keys,
    github_known_host_lines,
    github_proxy_ssh_config_lines,
    resolve_connect_command,
    resolve_proxy_uri,
    resolve_transport,
)


def _local_config(repository: Path, key: str) -> str | None:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository}",
            "-C",
            str(repository),
            "config",
            "--local",
            "--get",
            key,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        return result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
    if result.returncode == 1:
        return None
    raise RuntimeError(f"Unable to read local Git configuration {key!r}")


def invoke(
    repository: Path,
    git_arguments: list[str],
    *,
    ssh_transport: str | None = None,
    https_proxy: str | None = None,
    connect_command: str | None = None,
) -> int:
    assert_git_arguments(git_arguments)
    repository = repository.resolve()
    if not (repository / ".git").exists():
        probe = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "--git-dir"],
            check=False,
            capture_output=True,
        )
        if probe.returncode != 0:
            raise RuntimeError(f"not a Git repository: {repository}")
    base = [
        "git",
        "-c",
        f"safe.directory={repository}",
        "-C",
        str(repository),
    ]
    transport = resolve_transport(
        ssh_transport,
        os.environ.get("XAR_GIT_SSH_TRANSPORT"),
        _local_config(repository, "xar.sshTransport"),
    )
    if transport == "direct":
        return subprocess.run([*base, *git_arguments], check=False).returncode

    proxy_uri = resolve_proxy_uri(
        https_proxy,
        os.environ.get("XAR_GIT_HTTPS_PROXY") or os.environ.get("HTTPS_PROXY"),
        _local_config(repository, "xar.httpsProxy"),
    )
    connect = resolve_connect_command(
        connect_command
        or os.environ.get("XAR_GIT_CONNECT_COMMAND")
        or _local_config(repository, "xar.connectCommand")
    )
    base_ssh_command = _local_config(repository, "core.sshCommand")
    if not base_ssh_command:
        raise RuntimeError(
            "https-proxy transport requires core.sshCommand; run setup_git_operator.py first"
        )
    scratch_parent = os.environ.get("XAR_GIT_TEMP_ROOT")
    with tempfile.TemporaryDirectory(
        prefix="xar-git-operator-", dir=scratch_parent
    ) as temporary:
        scratch = Path(temporary)
        metadata = scratch / "github-meta.json"
        known_hosts = scratch / "known_hosts"
        ssh_config = scratch / "ssh_config"
        keys = get_github_ssh_host_keys(metadata, proxy_uri)
        known_hosts.write_text(
            "\n".join(github_known_host_lines(keys)) + "\n", encoding="utf-8"
        )
        ssh_config.write_text(
            "\n".join(
                github_proxy_ssh_config_lines(known_hosts, proxy_uri, connect)
            )
            + "\n",
            encoding="utf-8",
        )
        transport_command = add_ssh_config_argument(base_ssh_command, ssh_config)
        return subprocess.run(
            [
                *base,
                "-c",
                f"core.sshCommand={transport_command}",
                *git_arguments,
            ],
            check=False,
        ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--ssh-transport", choices=("direct", "https-proxy"))
    parser.add_argument("--https-proxy")
    parser.add_argument("--connect-command")
    parser.add_argument("git_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        return invoke(
            args.repository,
            args.git_arguments,
            ssh_transport=args.ssh_transport,
            https_proxy=args.https_proxy,
            connect_command=args.connect_command,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
