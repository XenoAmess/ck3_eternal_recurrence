<#
.SYNOPSIS
Runs Git for the current Windows operator with an exact process-local
safe.directory and the repository's shared SSH configuration.

.DESCRIPTION
This entry point does not depend on HOME, USERPROFILE, a per-user .gitconfig,
or a specific Windows account. Run setup_git_operator.ps1 once to configure
repository-local identity and SSH settings, then use this script from xenoa,
CodexSandboxOffline, or another authorized operator token.

The project forbids merge commits and force pushes. This wrapper rejects
`git merge`, `git pull` without an explicit `--rebase`, and force-push flags.

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 status --short --branch

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 -Repository Z:\workspace\open_kaishek fetch origin
#>
[CmdletBinding()]
param(
    [string]$Repository = (Get-Location).Path,
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$GitArguments
)

$ErrorActionPreference = "Stop"

if (-not $GitArguments -or $GitArguments.Count -eq 0) {
    throw "A Git subcommand is required"
}

$resolvedRepository = (Resolve-Path -LiteralPath $Repository -ErrorAction Stop).Path
$subcommand = $GitArguments[0].ToLowerInvariant()
if ($subcommand -eq "merge") {
    throw "git merge is forbidden in this project; fetch and rebase instead"
}
if ($subcommand -eq "pull" -and $GitArguments -notcontains "--rebase") {
    throw "git pull must include --rebase in this project"
}
if ($subcommand -eq "push") {
    $forceFlags = @($GitArguments | Where-Object {
        $_ -eq "-f" -or $_ -eq "--force" -or $_ -like "--force=*" -or
        $_ -eq "--force-with-lease" -or $_ -like "--force-with-lease=*"
    })
    if ($forceFlags.Count -gt 0) {
        throw "force push is forbidden in this project"
    }
}

$previousErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    & git -c "safe.directory=$resolvedRepository" -C $resolvedRepository @GitArguments
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}
exit $exitCode
