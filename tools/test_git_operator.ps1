$ErrorActionPreference = "Stop"
$repository = Split-Path -Parent $PSScriptRoot
$module = Join-Path $PSScriptRoot "git_operator_common.psm1"
$invokeScript = Join-Path $PSScriptRoot "invoke_git_operator.ps1"
Import-Module $module -Force

$assertions = 0

function Assert-Equal {
    param(
        [Parameter(Mandatory)]$Actual,
        [Parameter(Mandatory)]$Expected,
        [Parameter(Mandatory)][string]$Label
    )

    $script:assertions += 1
    if ($Actual -ne $Expected) {
        throw "$Label`: expected '$Expected', got '$Actual'"
    }
}

function Assert-Throws {
    param(
        [Parameter(Mandatory)][scriptblock]$Action,
        [Parameter(Mandatory)][string]$Pattern,
        [Parameter(Mandatory)][string]$Label
    )

    $script:assertions += 1
    try {
        & $Action
    } catch {
        if (($_ | Out-String) -notmatch $Pattern) {
            throw "$Label`: unexpected error: $($_ | Out-String)"
        }
        return
    }
    throw "$Label`: expected rejection"
}

function Assert-InvokeRejected {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Pattern,
        [Parameter(Mandatory)][string]$Label
    )

    $script:assertions += 1
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $invokeScript `
            -Repository $repository @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -eq 0) {
        throw "$Label`: forbidden invocation succeeded"
    }
    if (($output | Out-String) -notmatch $Pattern) {
        throw "$Label`: unexpected output: $($output | Out-String)"
    }
}

Assert-Equal `
    -Actual (Resolve-GitOperatorTransport -ExplicitValue "https-proxy" -EnvironmentValue "direct" -ConfiguredValue "direct") `
    -Expected "https-proxy" `
    -Label "explicit transport precedence"
Assert-Equal `
    -Actual (Resolve-GitOperatorTransport -EnvironmentValue "https-proxy" -ConfiguredValue "direct") `
    -Expected "https-proxy" `
    -Label "environment transport precedence"
Assert-Equal `
    -Actual (Resolve-GitOperatorTransport -ConfiguredValue "https-proxy") `
    -Expected "https-proxy" `
    -Label "configured transport"
Assert-Equal `
    -Actual (Resolve-GitOperatorTransport) `
    -Expected "direct" `
    -Label "default transport"

$proxy = Resolve-GitOperatorProxyUri -ExplicitValue "http://proxy.invalid:8080"
Assert-Equal -Actual $proxy.Host -Expected "proxy.invalid" -Label "proxy host"
Assert-Equal -Actual $proxy.Port -Expected 8080 -Label "proxy port"
Assert-Throws `
    -Action { Resolve-GitOperatorProxyUri -ExplicitValue "http://name:secret@proxy.invalid:8080" } `
    -Pattern "Proxy credentials are not accepted" `
    -Label "credential-bearing proxy"

$hostKey = "ssh-ed25519 AAAA"
$knownHostLines = @(New-GitHubKnownHostLines -HostKeys @($hostKey))
$expectedKnownHosts = @(
    "[github.com]:443 $hostKey",
    "[ssh.github.com]:443 $hostKey"
)
Assert-Equal `
    -Actual ($knownHostLines -join "`n") `
    -Expected ($expectedKnownHosts -join "`n") `
    -Label "known-host construction"

$configLines = @(New-GitHubProxySshConfigLines `
    -KnownHostsPath "C:\operator temp\known_hosts" `
    -ProxyUri $proxy `
    -ConnectCommand "C:\Git Tools\connect.exe")
$expectedConfig = @(
    "Host github.com ssh.github.com",
    "  HostName ssh.github.com",
    "  Port 443",
    "  User git",
    "  BatchMode yes",
    "  IdentitiesOnly yes",
    "  StrictHostKeyChecking yes",
    '  UserKnownHostsFile "C:/operator temp/known_hosts"',
    '  ProxyCommand "C:/Git Tools/connect.exe" -H proxy.invalid:8080 %h %p'
)
Assert-Equal `
    -Actual ($configLines -join "`n") `
    -Expected ($expectedConfig -join "`n") `
    -Label "proxy SSH config construction"
Assert-Equal `
    -Actual (Add-GitOperatorSshConfigArgument -BaseCommand "ssh-wrapper -KeyPath key" -ConfigPath "C:\operator temp\ssh_config") `
    -Expected 'ssh-wrapper -KeyPath key -F "C:/operator temp/ssh_config"' `
    -Label "core SSH command construction"

Assert-GitOperatorArguments -GitArguments @("pull", "--rebase", "origin", "main")
Assert-GitOperatorArguments -GitArguments @("push", "origin", "HEAD:main")
Assert-Throws `
    -Action { Assert-GitOperatorArguments -GitArguments @("merge", "origin/main") } `
    -Pattern "git merge is forbidden" `
    -Label "module merge policy"
Assert-Throws `
    -Action { Assert-GitOperatorArguments -GitArguments @("pull", "origin", "main") } `
    -Pattern "git pull must include --rebase" `
    -Label "module pull policy"
Assert-Throws `
    -Action { Assert-GitOperatorArguments -GitArguments @("push", "--force-with-lease", "origin", "main") } `
    -Pattern "force push is forbidden" `
    -Label "module force policy"
Assert-Throws `
    -Action { Assert-GitOperatorArguments -GitArguments @("push", "origin", "+HEAD:main") } `
    -Pattern "force push is forbidden" `
    -Label "module forced refspec policy"

Assert-InvokeRejected `
    -Arguments @("merge", "origin/main") `
    -Pattern "git merge is forbidden" `
    -Label "entrypoint merge policy"
Assert-InvokeRejected `
    -Arguments @("pull", "origin", "main") `
    -Pattern "git pull must include --rebase" `
    -Label "entrypoint pull policy"
Assert-InvokeRejected `
    -Arguments @("push", "--force", "origin", "main") `
    -Pattern "force push is forbidden" `
    -Label "entrypoint force policy"

"git operator tests passed ($assertions assertions; no network)"
