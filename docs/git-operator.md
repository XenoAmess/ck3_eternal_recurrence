# Git operator transport

`tools/setup_git_operator.ps1` configures repository-local identity, the
pre-provisioned SID-isolating SSH wrapper, and rebase-only pulls.
`tools/invoke_git_operator.ps1` is the required entry point for subsequent Git
commands. Neither script stores private keys in the repository or depends on a
particular Windows profile.

## Prerequisites

The external auth root is provisioned separately and contains
`git-ssh-wrapper.ps1` plus one repository-specific private key. Set its location
for the current process; do not commit it:

```powershell
$env:XAR_SHARED_GIT_AUTH_ROOT = $secureAuthRoot
$env:XAR_GIT_USER_NAME = $gitAuthorName
$env:XAR_GIT_USER_EMAIL = $gitAuthorEmail
```

Optional repository paths use `XAR_OPEN_KAISHEK_REPOSITORY` and
`XAR_PROMO_TOOLCHAIN_REPOSITORY`. If neither variable nor the corresponding
parameter is supplied, setup skips that optional repository. When the auth-root
variable is absent, setup derives a sibling directory named after the main
repository with `_shared_git_auth` appended.

## Transport selection

The selection order is an explicit `-SshTransport` argument,
`XAR_GIT_SSH_TRANSPORT`, local `xar.sshTransport`, then `direct`.

Direct SSH keeps the standard repository `core.sshCommand`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup_git_operator.ps1 `
  -SshTransport direct
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 `
  fetch origin
```

For an environment that denies direct SSH sockets but supplies a
credential-free HTTP CONNECT proxy, select `https-proxy`:

```powershell
$env:XAR_GIT_SSH_TRANSPORT = "https-proxy"
$env:XAR_GIT_HTTPS_PROXY = $env:HTTPS_PROXY
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup_git_operator.ps1 `
  -SkipGlobalSafeDirectory
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 `
  fetch origin
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 `
  pull --rebase origin master
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 `
  push origin HEAD:master
```

The proxy can instead be passed with `-HttpsProxy` or stored locally as
`xar.httpsProxy`. Proxy URIs containing credentials are rejected. Git for
Windows `connect.exe` is discovered relative to `git.exe`; an unusual install
can use `XAR_GIT_CONNECT_COMMAND`, `-ConnectCommand`, or local
`xar.connectCommand`. `XAR_GIT_PYTHON` or `-PythonCommand` selects a Python
executable when `python.exe` is not discoverable.

In proxy mode, each invocation:

1. retrieves `https://api.github.com/meta` with Python's default certificate
   verification through the selected proxy;
2. validates the published SSH key records and writes an ephemeral
   `known_hosts` file for GitHub's SSH-over-443 endpoint;
3. runs OpenSSH with `StrictHostKeyChecking yes`, `BatchMode yes`, and the
   external repository key wrapper through HTTP CONNECT; and
4. deletes the metadata, `known_hosts`, SSH config, and empty scratch directory
   in a `finally` block.

No repository or global SSH setting is weakened. `XAR_GIT_TEMP_ROOT` may point
to an existing writable scratch parent; otherwise the operating-system temp
directory is used.

## Policy and verification

The invocation wrapper rejects merges, pulls that do not explicitly rebase,
force flags, mirror pushes, and `+` force refspecs. A normal workflow is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 fetch origin
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 rebase origin/master
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 push --dry-run origin HEAD:master
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 push origin HEAD:master
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 ls-remote --exit-code origin refs/heads/master
```

The deterministic offline test covers transport precedence, proxy and SSH
command construction with mock host keys, and both module- and entrypoint-level
merge/rebase/force policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/test_git_operator.ps1
```
