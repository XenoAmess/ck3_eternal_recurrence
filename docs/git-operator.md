# Git operator transport

`tools/setup_git_operator.py` configures repository-local identity, a direct
OpenSSH command bound to the external repository key, and rebase-only pulls.
`tools/invoke_git_operator.py` is the guarded entry point for subsequent Git
commands. Neither program stores private keys in the repository or depends on a
particular Windows profile.

## Prerequisites

The external auth root is provisioned separately and contains one
repository-specific private key. Set `XAR_SHARED_GIT_AUTH_ROOT`,
`XAR_GIT_USER_NAME`, and `XAR_GIT_USER_EMAIL` in the calling process; do not
commit their values. Optional repository paths use
`XAR_OPEN_KAISHEK_REPOSITORY` and `XAR_PROMO_TOOLCHAIN_REPOSITORY`.

When the auth-root variable is absent, setup derives a sibling directory named
after the main repository with `_shared_git_auth` appended. The Python setup no
longer requires or accepts an external script wrapper.

## Transport selection

The selection order is an explicit `--ssh-transport` argument,
`XAR_GIT_SSH_TRANSPORT`, local `xar.sshTransport`, then `direct`.

Direct SSH:

```text
py tools/setup_git_operator.py --ssh-transport direct
py tools/invoke_git_operator.py fetch origin
```

For an environment that denies direct SSH sockets but supplies a
credential-free HTTP CONNECT proxy:

```text
set XAR_GIT_SSH_TRANSPORT=https-proxy
set XAR_GIT_HTTPS_PROXY=http://127.0.0.1:8080
py tools/setup_git_operator.py --skip-global-safe-directory
py tools/invoke_git_operator.py fetch origin
py tools/invoke_git_operator.py pull --rebase origin master
py tools/invoke_git_operator.py push origin HEAD:master
```

The proxy can instead be passed with `--https-proxy` or stored locally as
`xar.httpsProxy`. Proxy URIs containing credentials are rejected. Git for
Windows `connect.exe` is discovered relative to `git.exe`; an unusual install
can use `XAR_GIT_CONNECT_COMMAND`, `--connect-command`, or local
`xar.connectCommand`.

In proxy mode, each invocation:

1. retrieves `https://api.github.com/meta` with Python's default certificate
   verification through the selected proxy;
2. validates the published SSH key records and writes an ephemeral
   `known_hosts` file for GitHub's SSH-over-443 endpoint;
3. runs OpenSSH with strict host checking, batch mode, the external repository
   key, and HTTP CONNECT; and
4. deletes the metadata, `known_hosts`, SSH config, and scratch directory when
   the invocation ends.

## Policy and verification

The invocation wrapper rejects merges, pulls that do not explicitly rebase,
force flags, mirror pushes, and `+` force refspecs. A normal workflow is:

```text
py tools/invoke_git_operator.py fetch origin
py tools/invoke_git_operator.py rebase origin/master
py tools/invoke_git_operator.py push --dry-run origin HEAD:master
py tools/invoke_git_operator.py push origin HEAD:master
py tools/invoke_git_operator.py ls-remote --exit-code origin refs/heads/master
```

The deterministic offline test covers transport precedence, proxy and SSH
command construction, and both function- and entrypoint-level history policy:

```text
py tools/test_git_operator.py
```
