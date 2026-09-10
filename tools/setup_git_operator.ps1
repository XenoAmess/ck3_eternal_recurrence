<#
.SYNOPSIS
Configures and verifies one or more project repositories for the current
Windows operator without depending on that operator's profile or SID.

.DESCRIPTION
Repository-local identity, rebase-only pull behavior, transport selection, and
the existing SID-isolating SSH wrapper are shared by every operator. Each Git
command also injects its exact safe.directory, so -VerifyOnly remains usable
when the current account has no profile or writable global Git configuration.

Paths can be supplied as parameters or through XAR_OPEN_KAISHEK_REPOSITORY,
XAR_PROMO_TOOLCHAIN_REPOSITORY, and XAR_SHARED_GIT_AUTH_ROOT. Optional
repositories are skipped when no path is supplied. The script never prints
private-key contents and never fetches, rebases, commits, or pushes. The
optional push check uses git push --dry-run only when local HEAD already equals
the target remote branch.

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
    [string]$OpenKaishekRepository = $env:XAR_OPEN_KAISHEK_REPOSITORY,
    [string]$PromoRepository = $env:XAR_PROMO_TOOLCHAIN_REPOSITORY,
    [string]$AuthRoot = $env:XAR_SHARED_GIT_AUTH_ROOT,
    [string]$GitUserName = $env:XAR_GIT_USER_NAME,
    [string]$GitUserEmail = $env:XAR_GIT_USER_EMAIL,
    [ValidateSet("direct", "https-proxy")]
    [string]$SshTransport,
    [string]$HttpsProxy,
    [string]$ConnectCommand,
    [string]$PythonCommand,
    [switch]$VerifyOnly,
    [switch]$VerifyPushDryRun,
    [switch]$SkipGlobalSafeDirectory
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "git_operator_common.psm1") -Force

if (-not $MainRepository) {
    $MainRepository = Split-Path -Parent $PSScriptRoot
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

function Get-OptionalGitConfig {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$Key
    )

    $output = & git -c "safe.directory=$Repository" -C $Repository config --local --get $Key 2>$null
    if ($LASTEXITCODE -eq 0) {
        return ($output | Select-Object -First 1)
    }
    if ($LASTEXITCODE -eq 1) {
        return $null
    }
    throw "Unable to read local Git configuration '$Key' for $Repository"
}

function Invoke-OperatorGit {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$Transport,
        [Parameter(Mandatory)][string[]]$Arguments,
        [string]$Proxy,
        [string]$Connect,
        [string]$Python,
        [switch]$Capture
    )

    $operatorScript = Join-Path $PSScriptRoot "invoke_git_operator.ps1"
    $processArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $operatorScript,
        "-Repository", $Repository,
        "-SshTransport", $Transport
    )
    if ($Proxy) {
        $processArguments += @("-HttpsProxy", $Proxy)
    }
    if ($Connect) {
        $processArguments += @("-ConnectCommand", $Connect)
    }
    if ($Python) {
        $processArguments += @("-PythonCommand", $Python)
    }
    $processArguments += $Arguments

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & powershell.exe @processArguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        $detail = ($output | Out-String).Trim()
        throw "operator git $($Arguments -join ' ') failed for $Repository`: $detail"
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
    if ($known -notcontains (ConvertTo-GitOperatorPath $Repository)) {
        & git config --global --add safe.directory (ConvertTo-GitOperatorPath $Repository)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to add safe.directory for the current Windows operator: $Repository"
        }
    }
}

$repositories = New-Object System.Collections.Generic.List[object]
$repositories.Add(
    [pscustomobject]@{
        Name = "ck3_eternal_recurrence"
        Path = $MainRepository
        RemoteBranch = "master"
        KeyName = "ck3_eternal_recurrence_ed25519"
    }
)
if ($OpenKaishekRepository) {
    $repositories.Add(
    [pscustomobject]@{
        Name = "open_kaishek"
        Path = $OpenKaishekRepository
        RemoteBranch = "main"
        KeyName = "open_kaishek_ed25519"
    }
    )
}
if ($PromoRepository) {
    $repositories.Add(
    [pscustomobject]@{
        Name = "xar_promo_toolchain"
        Path = $PromoRepository
        RemoteBranch = "main"
        KeyName = "xar_promo_toolchain_ed25519"
    }
    )
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
if ($null -eq $identity.User) {
    throw "Current Windows operator has no SID"
}

foreach ($repository in $repositories) {
    $resolvedRepository = (Resolve-Path -LiteralPath $repository.Path).Path
    $effectiveUserName = if ($GitUserName) {
        $GitUserName
    } else {
        (& git -c "safe.directory=$resolvedRepository" -C $resolvedRepository config --get user.name 2>$null |
            Select-Object -First 1)
    }
    $effectiveUserEmail = if ($GitUserEmail) {
        $GitUserEmail
    } else {
        (& git -c "safe.directory=$resolvedRepository" -C $resolvedRepository config --get user.email 2>$null |
            Select-Object -First 1)
    }
    $configuredTransport = Get-OptionalGitConfig -Repository $resolvedRepository -Key "xar.sshTransport"
    $transport = Resolve-GitOperatorTransport `
        -ExplicitValue $SshTransport `
        -EnvironmentValue $env:XAR_GIT_SSH_TRANSPORT `
        -ConfiguredValue $configuredTransport
    $configuredProxy = Get-OptionalGitConfig -Repository $resolvedRepository -Key "xar.httpsProxy"
    $proxy = $null
    if ($transport -eq "https-proxy") {
        $proxy = Resolve-GitOperatorProxyUri `
            -ExplicitValue $HttpsProxy `
            -EnvironmentValue $(if ($env:XAR_GIT_HTTPS_PROXY) { $env:XAR_GIT_HTTPS_PROXY } else { $env:HTTPS_PROXY }) `
            -ConfiguredValue $configuredProxy
    }
    $configuredConnect = Get-OptionalGitConfig -Repository $resolvedRepository -Key "xar.connectCommand"
    $connect = if ($ConnectCommand) {
        $ConnectCommand
    } elseif ($env:XAR_GIT_CONNECT_COMMAND) {
        $env:XAR_GIT_CONNECT_COMMAND
    } else {
        $configuredConnect
    }

    if (-not $VerifyOnly) {
        if (-not $effectiveUserName -or -not $effectiveUserEmail) {
            throw "Git identity is unavailable; set XAR_GIT_USER_NAME and XAR_GIT_USER_EMAIL or pass -GitUserName and -GitUserEmail"
        }
        if (-not $AuthRoot) {
            $mainParent = Split-Path -Parent (Resolve-Path -LiteralPath $MainRepository).Path
            $mainName = Split-Path -Leaf (Resolve-Path -LiteralPath $MainRepository).Path
            $AuthRoot = Join-Path $mainParent "${mainName}_shared_git_auth"
        }
        $wrapper = Join-Path $AuthRoot "git-ssh-wrapper.ps1"
        $key = Join-Path $AuthRoot $repository.KeyName
        if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) {
            throw "Shared SSH wrapper is unavailable: $wrapper"
        }
        if (-not (Test-Path -LiteralPath $key -PathType Leaf)) {
            throw "Repository SSH key is unavailable for $($repository.Name)"
        }
        $sshCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}" -KeyPath "{1}"' -f `
            (ConvertTo-GitOperatorPath $wrapper), (ConvertTo-GitOperatorPath $key)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "user.name", $effectiveUserName)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "user.email", $effectiveUserEmail)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "core.sshCommand", $sshCommand)
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "pull.rebase", "true")
        Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "xar.sshTransport", $transport)
        if ($PSBoundParameters.ContainsKey("HttpsProxy") -and $proxy) {
            Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "xar.httpsProxy", $proxy.AbsoluteUri)
        }
        if ($PSBoundParameters.ContainsKey("ConnectCommand")) {
            $resolvedConnect = Resolve-GitOperatorConnectCommand -ExplicitValue $ConnectCommand
            Invoke-Git -Repository $resolvedRepository -Arguments @("config", "--local", "xar.connectCommand", $resolvedConnect)
            $connect = $resolvedConnect
        }
        if (-not $SkipGlobalSafeDirectory) {
            Add-CurrentUserSafeDirectory $resolvedRepository
        }
    }

    $status = Invoke-Git -Repository $resolvedRepository -Arguments @("status", "--short", "--branch", "--untracked-files=no") -Capture
    $remote = Invoke-OperatorGit `
        -Repository $resolvedRepository `
        -Transport $transport `
        -Proxy $(if ($proxy) { $proxy.AbsoluteUri } else { $null }) `
        -Connect $connect `
        -Python $PythonCommand `
        -Arguments @("ls-remote", "--exit-code", "origin", "refs/heads/$($repository.RemoteBranch)") `
        -Capture

    $localHead = (Invoke-Git -Repository $resolvedRepository -Arguments @("rev-parse", "HEAD") -Capture | Select-Object -First 1).Trim()
    $remoteFields = (($remote | Select-Object -First 1) -split "\s+")
    $synchronized = $localHead -eq $remoteFields[0]
    $pushDryRun = "not-requested"
    if ($VerifyPushDryRun) {
        if ($synchronized) {
            Invoke-OperatorGit `
                -Repository $resolvedRepository `
                -Transport $transport `
                -Proxy $(if ($proxy) { $proxy.AbsoluteUri } else { $null }) `
                -Connect $connect `
                -Python $PythonCommand `
                -Arguments @("push", "--dry-run", "origin", "HEAD:$($repository.RemoteBranch)")
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
        ssh_transport = $transport
        synchronized = $synchronized
        push_dry_run = $pushDryRun
        status = ($status -join "`n")
    }
}
