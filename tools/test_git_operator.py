from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

from git_operator_common import (
    add_ssh_config_argument,
    assert_git_arguments,
    github_known_host_lines,
    github_proxy_ssh_config_lines,
    resolve_proxy_uri,
    resolve_transport,
)


ROOT = Path(__file__).resolve().parents[1]
ENTRY = Path(__file__).with_name("invoke_git_operator.py")


class GitOperatorTests(unittest.TestCase):
    def test_transport_precedence(self) -> None:
        self.assertEqual(resolve_transport("https-proxy", "direct", "direct"), "https-proxy")
        self.assertEqual(resolve_transport(None, "https-proxy", "direct"), "https-proxy")
        self.assertEqual(resolve_transport(None, None, "https-proxy"), "https-proxy")
        self.assertEqual(resolve_transport(None, None, None), "direct")

    def test_proxy_and_ssh_config(self) -> None:
        proxy = resolve_proxy_uri("http://proxy.invalid:8080", None, None)
        self.assertEqual(proxy, "http://proxy.invalid:8080")
        with self.assertRaisesRegex(ValueError, "credentials"):
            resolve_proxy_uri("http://name:secret@proxy.invalid:8080", None, None)
        host_key = "ssh-ed25519 AAAA"
        self.assertEqual(
            github_known_host_lines([host_key]),
            [f"[github.com]:443 {host_key}", f"[ssh.github.com]:443 {host_key}"],
        )
        self.assertEqual(
            github_proxy_ssh_config_lines(
                r"C:\operator temp\known_hosts",
                proxy,
                r"C:\Git Tools\connect.exe",
            ),
            [
                "Host github.com ssh.github.com",
                "  HostName ssh.github.com",
                "  Port 443",
                "  User git",
                "  BatchMode yes",
                "  IdentitiesOnly yes",
                "  StrictHostKeyChecking yes",
                '  UserKnownHostsFile "C:/operator temp/known_hosts"',
                '  ProxyCommand "C:/Git Tools/connect.exe" -H proxy.invalid:8080 %h %p',
            ],
        )
        self.assertEqual(
            add_ssh_config_argument(
                "ssh-wrapper -KeyPath key", r"C:\operator temp\ssh_config"
            ),
            'ssh-wrapper -KeyPath key -F "C:/operator temp/ssh_config"',
        )

    def test_history_policy(self) -> None:
        assert_git_arguments(["pull", "--rebase", "origin", "master"])
        assert_git_arguments(["push", "origin", "HEAD:master"])
        for arguments, message in (
            (["merge", "origin/master"], "git merge is forbidden"),
            (["pull", "origin", "master"], "git pull must include --rebase"),
            (["push", "--force-with-lease", "origin", "master"], "force push is forbidden"),
            (["push", "origin", "+HEAD:master"], "force push is forbidden"),
        ):
            with self.assertRaisesRegex(ValueError, message):
                assert_git_arguments(arguments)

    def test_entrypoint_rejects_forbidden_commands_without_network(self) -> None:
        for arguments, message in (
            (["merge", "origin/master"], "git merge is forbidden"),
            (["pull", "origin", "master"], "git pull must include --rebase"),
            (["push", "--force", "origin", "master"], "force push is forbidden"),
        ):
            completed = subprocess.run(
                [sys.executable, str(ENTRY), "--repository", str(ROOT), *arguments],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(message, completed.stderr)


if __name__ == "__main__":
    unittest.main()
