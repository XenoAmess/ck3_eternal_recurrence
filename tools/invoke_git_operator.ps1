<#
.SYNOPSIS
Runs Git for the current Windows operator with an exact process-local
safe.directory and the repository's shared SSH configuration.

.DESCRIPTION
This entry point does not depend on HOME, USERPROFILE, a per-user .gitconfig,
or a specific Windows account. Run setup_git_operator.ps1 once to configure
repository-local identity and SSH settings, then use this script from any
authorized operator token.

The SSH transport is selected in this order: -SshTransport,
XAR_GIT_SSH_TRANSPORT, local xar.sshTransport, then direct. The https-proxy
mode uses a credential-free HTTP CONNECT proxy, retrieves GitHub's published
SSH host keys over certificate-verified HTTPS, enforces strict host checking,
and removes its metadata, known-hosts, and SSH-config scratch files.

The project forbids merge commits and force pushes. This wrapper rejects
`git merge`, `git pull` without an explicit `--rebase`, and force-push flags.

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 status --short --branch

.EXAMPLE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/invoke_git_operator.ps1 -Repository $env:XAR_OPEN_KAISHEK_REPOSITORY fetch origin
#>
[CmdletBinding()]
param(
    [string]$Repository = (Get-Location).Path,
    [ValidateSet("direct", "https-proxy")]
    [string]$SshTransport,
    [string]$HttpsProxy,
    [string]$ConnectCommand,
    [string]$PythonCommand,
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$GitArguments
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "git_operator_common.psm1") -Force

Assert-GitOperatorArguments -GitArguments $GitArguments
$resolvedRepository = (Resolve-Path -LiteralPath $Repository -ErrorAction Stop).Path

function Get-OptionalLocalConfig {
    param([Parameter(Mandatory)][string]$Key)

    $value = & git -c "safe.directory=$resolvedRepository" -C $resolvedRepository config --local --get $Key 2>$null
    if ($LASTEXITCODE -eq 0) {
        return ($value | Select-Object -First 1)
    }
    if ($LASTEXITCODE -eq 1) {
        return $null
    }
    throw "Unable to read local Git configuration '$Key'"
}

$configuredTransport = Get-OptionalLocalConfig -Key "xar.sshTransport"
$transport = Resolve-GitOperatorTransport `
    -ExplicitValue $SshTransport `
    -EnvironmentValue $env:XAR_GIT_SSH_TRANSPORT `
    -ConfiguredValue $configuredTransport

if ($transport -eq "direct") {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & git -c "safe.directory=$resolvedRepository" -C $resolvedRepository @GitArguments
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    exit $exitCode
}

$configuredProxy = Get-OptionalLocalConfig -Key "xar.httpsProxy"
$proxy = Resolve-GitOperatorProxyUri `
    -ExplicitValue $HttpsProxy `
    -EnvironmentValue $(if ($env:XAR_GIT_HTTPS_PROXY) { $env:XAR_GIT_HTTPS_PROXY } else { $env:HTTPS_PROXY }) `
    -ConfiguredValue $configuredProxy
$configuredConnectCommand = Get-OptionalLocalConfig -Key "xar.connectCommand"
$effectiveConnectCommand = Resolve-GitOperatorConnectCommand $(
    if ($ConnectCommand) {
        $ConnectCommand
    } elseif ($env:XAR_GIT_CONNECT_COMMAND) {
        $env:XAR_GIT_CONNECT_COMMAND
    } else {
        $configuredConnectCommand
    }
)
$baseSshCommand = Get-OptionalLocalConfig -Key "core.sshCommand"
if (-not $baseSshCommand) {
    throw "https-proxy transport requires core.sshCommand; run setup_git_operator.ps1 first"
}

$scratchParent = if ($env:XAR_GIT_TEMP_ROOT) {
    (Resolve-Path -LiteralPath $env:XAR_GIT_TEMP_ROOT -ErrorAction Stop).Path
} else {
    [IO.Path]::GetTempPath()
}
$scratchRoot = Join-Path $scratchParent ("xar-git-operator-" + [Guid]::NewGuid().ToString("N"))
$metadataPath = Join-Path $scratchRoot "github-meta.json"
$knownHostsPath = Join-Path $scratchRoot "known_hosts"
$sshConfigPath = Join-Path $scratchRoot "ssh_config"
$exitCode = 1
try {
    New-Item -ItemType Directory -Path $scratchRoot | Out-Null

    $hostKeys = Get-GitHubSshHostKeys `
        -OutputPath $metadataPath `
        -ProxyUri $proxy `
        -PythonCommand $(if ($PythonCommand) { $PythonCommand } else { $env:XAR_GIT_PYTHON })
    $knownHostLines = New-GitHubKnownHostLines -HostKeys $hostKeys
    [IO.File]::WriteAllLines($knownHostsPath, $knownHostLines, (New-Object Text.UTF8Encoding($false)))
    $sshConfigLines = New-GitHubProxySshConfigLines `
        -KnownHostsPath $knownHostsPath `
        -ProxyUri $proxy `
        -ConnectCommand $effectiveConnectCommand
    [IO.File]::WriteAllLines($sshConfigPath, $sshConfigLines, (New-Object Text.UTF8Encoding($false)))
    $transportCommand = Add-GitOperatorSshConfigArgument `
        -BaseCommand $baseSshCommand `
        -ConfigPath $sshConfigPath

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & git -c "safe.directory=$resolvedRepository" -c "core.sshCommand=$transportCommand" `
            -C $resolvedRepository @GitArguments
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
} finally {
    foreach ($path in @($metadataPath, $knownHostsPath, $sshConfigPath)) {
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            Remove-Item -LiteralPath $path -Force
        }
    }
    if (Test-Path -LiteralPath $scratchRoot -PathType Container) {
        $remaining = @(Get-ChildItem -LiteralPath $scratchRoot -Force)
        if ($remaining.Count -eq 0) {
            Remove-Item -LiteralPath $scratchRoot -Force
        } else {
            throw "Git operator scratch directory was not empty after cleanup: $scratchRoot"
        }
    }
}
exit $exitCode
