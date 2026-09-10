Set-StrictMode -Version Latest

function ConvertTo-GitOperatorPath {
    param([Parameter(Mandatory)][string]$Path)

    return $Path.Replace("\", "/")
}

function Assert-GitOperatorArguments {
    param([Parameter(Mandatory)][string[]]$GitArguments)

    if (-not $GitArguments -or $GitArguments.Count -eq 0) {
        throw "A Git subcommand is required"
    }

    $subcommand = $GitArguments[0].ToLowerInvariant()
    if ($subcommand -eq "merge") {
        throw "git merge is forbidden in this project; fetch and rebase instead"
    }
    if ($subcommand -eq "pull") {
        $rebaseArguments = @($GitArguments | Where-Object {
            $_ -eq "--rebase" -or ($_ -like "--rebase=*" -and $_ -notin @("--rebase=false", "--rebase=no"))
        })
        if ($rebaseArguments.Count -eq 0) {
            throw "git pull must include --rebase in this project"
        }
    }
    if ($subcommand -eq "push") {
        $forceArguments = @($GitArguments | Where-Object {
            $_ -eq "-f" -or $_ -eq "--force" -or $_ -like "--force=*" -or
            $_ -eq "--force-with-lease" -or $_ -like "--force-with-lease=*" -or
            $_ -eq "--mirror" -or $_ -like "+*"
        })
        if ($forceArguments.Count -gt 0) {
            throw "force push is forbidden in this project"
        }
    }
}

function Resolve-GitOperatorTransport {
    param(
        [string]$ExplicitValue,
        [string]$EnvironmentValue,
        [string]$ConfiguredValue
    )

    $selected = @($ExplicitValue, $EnvironmentValue, $ConfiguredValue, "direct") |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -First 1
    $normalized = $selected.Trim().ToLowerInvariant()
    if ($normalized -notin @("direct", "https-proxy")) {
        throw "Unsupported SSH transport '$selected'; expected direct or https-proxy"
    }
    return $normalized
}

function Resolve-GitOperatorProxyUri {
    param(
        [string]$ExplicitValue,
        [string]$EnvironmentValue,
        [string]$ConfiguredValue
    )

    $selected = @($ExplicitValue, $EnvironmentValue, $ConfiguredValue) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -First 1
    if (-not $selected) {
        throw "https-proxy transport requires XAR_GIT_HTTPS_PROXY, HTTPS_PROXY, -HttpsProxy, or local xar.httpsProxy"
    }

    $uri = $null
    if (-not [Uri]::TryCreate($selected, [UriKind]::Absolute, [ref]$uri) -or
        $uri.Scheme -ne "http" -or -not $uri.Host) {
        throw "The HTTPS proxy must be an absolute http:// URI"
    }
    if ($uri.UserInfo) {
        throw "Proxy credentials are not accepted; use a credential-free local proxy endpoint"
    }
    if (($uri.AbsolutePath -and $uri.AbsolutePath -ne "/") -or $uri.Query -or $uri.Fragment) {
        throw "The HTTPS proxy URI must contain only scheme, host, and port"
    }
    return $uri
}

function Resolve-GitOperatorConnectCommand {
    param([string]$ExplicitValue)

    if ($ExplicitValue) {
        return (Resolve-Path -LiteralPath $ExplicitValue -ErrorAction Stop).Path
    }

    $command = Get-Command connect.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) {
        return $command.Source
    }

    $gitCommand = Get-Command git.exe -ErrorAction Stop | Select-Object -First 1
    $gitRoot = Split-Path -Parent (Split-Path -Parent $gitCommand.Source)
    $candidate = Join-Path $gitRoot "mingw64\bin\connect.exe"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        return (Resolve-Path -LiteralPath $candidate).Path
    }
    throw "Git for Windows connect.exe is unavailable; set XAR_GIT_CONNECT_COMMAND or local xar.connectCommand"
}

function New-GitHubKnownHostLines {
    param([Parameter(Mandatory)][string[]]$HostKeys)

    if (-not $HostKeys -or $HostKeys.Count -eq 0) {
        throw "GitHub metadata returned no SSH host keys"
    }
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($key in $HostKeys) {
        if ($key -notmatch "^(ssh-ed25519|ecdsa-sha2-nistp256|ssh-rsa) [A-Za-z0-9+/]+={0,3}$") {
            throw "GitHub metadata returned an unsupported SSH host-key record"
        }
        $lines.Add("[github.com]:443 $key")
        $lines.Add("[ssh.github.com]:443 $key")
    }
    return @($lines)
}

function New-GitHubProxySshConfigLines {
    param(
        [Parameter(Mandatory)][string]$KnownHostsPath,
        [Parameter(Mandatory)][Uri]$ProxyUri,
        [Parameter(Mandatory)][string]$ConnectCommand
    )

    foreach ($value in @($KnownHostsPath, $ConnectCommand)) {
        if ($value -match '["\r\n]') {
            throw "SSH transport paths cannot contain quotes or newlines"
        }
    }
    $knownHosts = ConvertTo-GitOperatorPath $KnownHostsPath
    $connect = ConvertTo-GitOperatorPath $ConnectCommand
    $proxyHost = if ($ProxyUri.Host.Contains(":")) { "[$($ProxyUri.Host)]" } else { $ProxyUri.Host }
    return @(
        "Host github.com ssh.github.com",
        "  HostName ssh.github.com",
        "  Port 443",
        "  User git",
        "  BatchMode yes",
        "  IdentitiesOnly yes",
        "  StrictHostKeyChecking yes",
        "  UserKnownHostsFile `"$knownHosts`"",
        "  ProxyCommand `"$connect`" -H ${proxyHost}:$($ProxyUri.Port) %h %p"
    )
}

function Add-GitOperatorSshConfigArgument {
    param(
        [Parameter(Mandatory)][string]$BaseCommand,
        [Parameter(Mandatory)][string]$ConfigPath
    )

    if ($ConfigPath -match '["\r\n]') {
        throw "SSH config path cannot contain quotes or newlines"
    }
    return "$BaseCommand -F `"$(ConvertTo-GitOperatorPath $ConfigPath)`""
}

function Get-GitHubSshHostKeys {
    param(
        [Parameter(Mandatory)][string]$OutputPath,
        [Parameter(Mandatory)][Uri]$ProxyUri,
        [string]$PythonCommand
    )

    if (-not $PythonCommand) {
        $python = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $python) {
            throw "python.exe is required to retrieve GitHub host keys with certificate verification"
        }
        $PythonCommand = $python.Source
    } else {
        $PythonCommand = (Resolve-Path -LiteralPath $PythonCommand -ErrorAction Stop).Path
    }

    $pythonCode = "import pathlib, ssl, sys, urllib.request; request = urllib.request.Request('https://api.github.com/meta', headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'xar-git-operator'}); context = ssl.create_default_context(); proxy = urllib.request.ProxyHandler({'http': sys.argv[2], 'https': sys.argv[2]}); https = urllib.request.HTTPSHandler(context=context); opener = urllib.request.build_opener(proxy, https); pathlib.Path(sys.argv[1]).write_bytes(opener.open(request, timeout=20).read())"
    & $PythonCommand -c $pythonCode $OutputPath $ProxyUri.AbsoluteUri
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to retrieve GitHub SSH host keys over certificate-verified HTTPS"
    }
    $metadata = Get-Content -Raw -LiteralPath $OutputPath | ConvertFrom-Json
    return @($metadata.ssh_keys)
}

Export-ModuleMember -Function @(
    "ConvertTo-GitOperatorPath",
    "Assert-GitOperatorArguments",
    "Resolve-GitOperatorTransport",
    "Resolve-GitOperatorProxyUri",
    "Resolve-GitOperatorConnectCommand",
    "New-GitHubKnownHostLines",
    "New-GitHubProxySshConfigLines",
    "Add-GitOperatorSshConfigArgument",
    "Get-GitHubSshHostKeys"
)
