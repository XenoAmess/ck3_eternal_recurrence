<#
.SYNOPSIS
Configures and verifies the three project repositories for the current Windows
operator without depending on that operator's profile or SID.

.DESCRIPTION
Repository-local identity, rebase-only pull behavior, and the existing
SID-isolating SSH wrapper are shared by every operator. Each Git command also
injects its exact safe.directory, so -VerifyOnly remains usable when the
current account has no profile or writable global Git configuration.

Paths can be supplied as parameters or through XAR_OPEN_KAISHEK_REPOSITORY,
XAR_PROMO_TOOLCHAIN_REPOSITORY, and XAR_SHARED_GIT_AUTH_ROOT. The script never
prints private-key contents and never fetches, rebases, commits, or pushes.
The optional push check uses git push --dry-run only when local HEAD already
equals the target remote branch.

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup_git_operator.ps1

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup_git_operator.ps1 -VerifyOnly -VerifyPushDryRun

If a sandbox token has no writable user profile, pass
`-SkipGlobalSafeDirectory` and use tools/invoke_git_operator.ps1 for subsequent
status, fetch, rebase, commit, and push commands.
#>
[CmdletBinding()]
param(
    [string]$MainRepository,
    [string]$OpenKaishekRepository = $(
        if ($env:XAR_OPEN_KAISHEK_REPOSITORY) {
            $env:XAR_OPEN_KAISHEK_REPOSITORY
        } else {
            "Z:\workspace\open_kaishek"
        }
    ),
    [string]$PromoRepository = $(
        if ($env:XAR_PROMO_TOOLCHAIN_REPOSITORY) {
            $env:XAR_PROMO_TOOLCHAIN_REPOSITORY
        } else {
            "Z:\workspace\xar_promo_toolchain"
        }
    ),
    [string]$AuthRoot = $(
        if ($env:XAR_SHARED_GIT_AUTH_ROOT) {
            $env:XAR_SHARED_GIT_AUTH_ROOT
        } else {
            "Z:\ck3_mod_rewrite_shared_git_auth"
        }
    ),
    [string]$GitUserName = "XenoAmess",
    [string]$GitUserEmail = "xenoamess@gmail.com",
    [switch]$VerifyOnly,
    [switch]$VerifyPushDryRun,
    [switch]$SkipGlobalSafeDirectory
)

$ErrorActionPreference = "Stop"

if (-not $MainRepository) {
    $MainRepository = Split-Path -Parent $PSScriptRoot
}

function Convert-ToGitPath {
    param([Parameter(Mandatory)][string]$Path)

    return $Path.Replace("\", "/")
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string[]]$Arguments,
        [switch]$Capture
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & git -c "safe.directory=$Repository" -C $Repository @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        $detail = ($output | Out-String).Trim()
        throw "git $($Arguments -join ' ') failed for $Repository`: $detail"
    }
    if ($Capture) {
        return @($output)
    }
}

function Add-CurrentUserSafeDirectory {
    param([Parameter(Mandatory)][string]$Repository)

    $known = @(& git config --global --get-all safe.directory 2>$null)
    if ($LASTEXITCODE -notin @(0, 1)) {
        throw "Unable to read the current operator's global Git configuration"
    }
    if ($known -notcontains (Convert-ToGitPath $Repository)) {
        & git config --global --add safe.directory (Convert-ToGitPath $Repository)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to add safe.directory for the current Windows operator: $Repository"
        }
    }
}

$wrapper = Join-Path $AuthRoot "git-ssh-wrapper.ps1"
$repositories = @(
    [pscustomobject]@{
        Name = "ck3_eternal_recurrence"
        Path = $MainRepository
        RemoteBranch = "master"
        Key = Join-Path $AuthRoot "ck3_eternal_recurrence_ed25519"
    },
    [pscustomobject]@{
        Name = "open_kaishek"
        Path = $OpenKaishekRepository
        RemoteBranch = "main"
        Key = Join-Path $AuthRoot "open_kaishek_ed25519"
    },
    [pscustomobject]@{
        Name = "xar_promo_toolchain"
        Path = $PromoRepository
        RemoteBranch = "main"
        Key = Join-Path $AuthRoot "xar_promo_toolchain_ed25519"
    }
)

if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) {
    throw "Shared SSH wrapper is unavailable: $wrapper"
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
if ($null -eq $identity.User) {
    throw "Current Windows operator has no SID"
}

foreach ($repository in $repositories) {
    $resolvedRepository = (Resolve-Path -LiteralPath $repository.Path).Path
    if (-not (Test-Path -LiteralPath $repository.Key -PathType Leaf)) {
        throw "Repository SSH key is unavailable for $($repository.Name)"
    }

    if (-not $VerifyOnly) {
        $sshCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}" -KeyPath "{1}"' -f `
            (Convert-ToGitPath $wrapper), (Convert-ToGitPath $repository.Key)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "user.name", $GitUserName)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "user.email", $GitUserEmail)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "core.sshCommand", $sshCommand)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "pull.rebase", "true")
        if (-not $SkipGlobalSafeDirectory) {
            Add-CurrentUserSafeDirectory $resolvedRepository
        }
    }

    $status = Invoke-Git -Repository $resolvedRepository -Arguments @("status", "--short", "--branch", "--untracked-files=no") -Capture
    $remote = Invoke-Git -Repository $resolvedRepository -Arguments @(
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/heads/$($repository.RemoteBranch)"
    ) -Capture

    $localHead = (Invoke-Git -Repository $resolvedRepository -Arguments @("rev-parse", "HEAD") -Capture | Select-Object -First 1).Trim()
    $remoteFields = (($remote | Select-Object -First 1) -split "\s+")
    $synchronized = $localHead -eq $remoteFields[0]
    $pushDryRun = "not-requested"
    if ($VerifyPushDryRun) {
        if ($synchronized) {
            Invoke-Git -Repository $resolvedRepository -Arguments @(
                "push",
                "--dry-run",
                "origin",
                "HEAD:$($repository.RemoteBranch)"
            )
            $pushDryRun = "ok"
        } else {
            $pushDryRun = "skipped-remote-ahead"
        }
    }
    [pscustomobject]@{
        repository = $repository.Name
        path = $resolvedRepository
        windows_identity = $identity.Name
        windows_sid = $identity.User.Value
        status_ok = $true
        ls_remote_ok = $true
        local_head = $localHead
        remote_head = $remoteFields[0]
        remote_branch = $repository.RemoteBranch
        synchronized = $synchronized
        push_dry_run = $pushDryRun
        status = ($status -join "`n")
    }
}
