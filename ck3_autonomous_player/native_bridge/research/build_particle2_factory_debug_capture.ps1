param(
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "",
    [Parameter(Mandatory = $false)]
    [switch]$DebugBuild
)

$ErrorActionPreference = "Stop"
$researchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePath = Join-Path $researchRoot "particle2_factory_debug_capture.cpp"
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Missing source: $sourcePath"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $researchRoot "build-particle2-factory-debug-capture\particle2_factory_debug_capture.exe"
}
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputParent = Split-Path -Parent $resolvedOutput
New-Item -ItemType Directory -Path $outputParent -Force | Out-Null

$vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw "vswhere.exe is unavailable"
}
$env:PATH = "$(Split-Path -Parent $vswhere);$env:PATH"
$installation = (& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
if ([string]::IsNullOrWhiteSpace($installation)) {
    throw "No x64 MSVC installation found"
}
$developerShell = Join-Path $installation "Common7\Tools\VsDevCmd.bat"
if (-not (Test-Path -LiteralPath $developerShell -PathType Leaf)) {
    throw "VsDevCmd.bat is unavailable: $developerShell"
}

$optimization = if ($DebugBuild) { "/Od /Zi" } else { "/O2" }
$command = 'call "{0}" -no_logo -arch=amd64 >nul && cl.exe /nologo /std:c++20 /EHsc /W4 /WX {1} /DUNICODE /D_UNICODE "{2}" /Fe:"{3}" bcrypt.lib' -f $developerShell, $optimization, $sourcePath, $resolvedOutput
& cmd.exe /d /s /c $command
if ($LASTEXITCODE -ne 0) {
    throw "MSVC build failed with exit code $LASTEXITCODE"
}

$binary = Get-Item -LiteralPath $resolvedOutput
$hash = (Get-FileHash -LiteralPath $resolvedOutput -Algorithm SHA256).Hash
[pscustomobject]@{
    Output = $binary.FullName
    Bytes = $binary.Length
    Sha256 = $hash
    DebugBuild = [bool]$DebugBuild
}
