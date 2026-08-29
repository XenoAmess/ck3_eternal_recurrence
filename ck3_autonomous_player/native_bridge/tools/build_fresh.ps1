[CmdletBinding()]
param(
    [string]$BuildDir,
    [ValidateSet("Debug", "Release", "RelWithDebInfo", "MinSizeRel")]
    [string]$Configuration = "Release",
    [switch]$SkipTests,
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = [System.IO.Path]::GetFullPath((Join-Path $scriptDir ".."))

function Repair-NinjaMsvcDependencyPrefix {
    param(
        [Parameter(Mandatory = $true)][string]$BuildRoot,
        [Parameter(Mandatory = $true)][string]$CompilerPath
    )

    $compilerDirectory = Split-Path -Parent $CompilerPath
    $uiLocaleIds = @(
        Get-ChildItem -LiteralPath $compilerDirectory -Directory -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -match "^[0-9]+$" -and
                (Test-Path -LiteralPath (Join-Path $_.FullName "clui.dll") -PathType Leaf)
            } |
            ForEach-Object { $_.Name }
    )

    if ($uiLocaleIds -contains "1033") {
        return "vslang-1033"
    }
    if ($uiLocaleIds -notcontains "2052") {
        # Other localized toolchains retain CMake's detected value. The
        # post-build Ninja dependency assertion remains the authority.
        return "cmake-detected"
    }

    # MSVC 19.51 installations with only the 2052 resource emit the Chinese
    # /showIncludes prefix as UTF-8 even when VSLANG=1033. CMake 4.3 decodes
    # those bytes through the system ANSI code page, then writes that mojibake
    # to rules.ninja. Reverse exactly that conversion before Ninja compiles;
    # do not weaken the dependency database gate below.
    $rulesPath = Join-Path $BuildRoot "CMakeFiles\rules.ninja"
    if (-not (Test-Path -LiteralPath $rulesPath -PathType Leaf)) {
        throw "Ninja rules file is missing after configure: $rulesPath"
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $rules = [System.IO.File]::ReadAllText($rulesPath, $utf8NoBom)
    $matches = [System.Text.RegularExpressions.Regex]::Matches(
        $rules,
        "(?m)^msvc_deps_prefix = (?<value>[^\r\n]*)\r?$"
    )
    if ($matches.Count -ne 1) {
        throw "expected exactly one msvc_deps_prefix in $rulesPath"
    }

    $valueGroup = $matches[0].Groups["value"]
    $generatedPrefix = $valueGroup.Value
    # Keep the script ASCII so Windows PowerShell 5.1 does not decode an
    # unmarked UTF-8 .ps1 through code page 936 before evaluating it.
    $expected2052Prefix = [System.Text.Encoding]::UTF8.GetString(
        [System.Convert]::FromBase64String("5rOo5oSPOiDljIXlkKvmlofku7Y6")
    )
    if ($generatedPrefix.StartsWith($expected2052Prefix) -and
        $generatedPrefix.Substring($expected2052Prefix.Length).Trim().Length -eq 0) {
        return "cmake-detected-2052-utf8"
    }

    $repairedPrefix = [System.Text.Encoding]::UTF8.GetString(
        [System.Text.Encoding]::Default.GetBytes($generatedPrefix)
    )
    if (-not $repairedPrefix.StartsWith($expected2052Prefix) -or
        $repairedPrefix.Substring($expected2052Prefix.Length).Trim().Length -ne 0) {
        throw "could not recover the 2052 MSVC /showIncludes prefix in $rulesPath"
    }

    if ($repairedPrefix -ne $generatedPrefix) {
        $rules = $rules.Substring(0, $valueGroup.Index) +
            $repairedPrefix +
            $rules.Substring($valueGroup.Index + $valueGroup.Length)
        [System.IO.File]::WriteAllText($rulesPath, $rules, $utf8NoBom)
    }
    return "repaired-2052-utf8"
}

if ([string]::IsNullOrWhiteSpace($BuildDir)) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
    $BuildDir = Join-Path $sourceDir ("build-fresh-{0}-{1}" -f $stamp, $suffix)
} elseif (-not [System.IO.Path]::IsPathRooted($BuildDir)) {
    $BuildDir = Join-Path (Get-Location).Path $BuildDir
}
$buildDirPath = [System.IO.Path]::GetFullPath($BuildDir)

# The helper deliberately refuses every pre-existing path. The production
# failure this prevents was caused by a public Bindings layout change being
# linked with objects retained from an older incremental build.
if (Test-Path -LiteralPath $buildDirPath) {
    throw "fresh native bridge build directory already exists: $buildDirPath"
}

$dependencyObjects = @(
    "CMakeFiles/xar_ck3_bridge.dir/src/ck3_11906.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/ck3_11906_adapter.cpp.obj"
)

$plan = [ordered]@{
    source_dir = $sourceDir
    build_dir = $buildDirPath
    generator = "Ninja"
    configuration = $Configuration
    msvc_output_language = "1033"
    msvc_dependency_prefix_strategy = "vslang-1033-with-2052-utf8-repair"
    fresh_directory_required = $true
    source_fingerprint_required = $true
    dependency_header = "ck3_11906.hpp"
    dependency_objects = $dependencyObjects
    tests_enabled = (-not $SkipTests)
}

if ($PlanOnly) {
    $plan | ConvertTo-Json -Depth 4
    return
}

function Get-NativeBridgeSourceFingerprint {
    param([Parameter(Mandatory = $true)][string]$Root)

    $files = @((Get-Item -LiteralPath (Join-Path $Root "CMakeLists.txt")))
    foreach ($tree in @("include", "src")) {
        $files += Get-ChildItem -LiteralPath (Join-Path $Root $tree) -Recurse -File |
            Where-Object { $_.Extension -in @(".cpp", ".hpp", ".h", ".c") }
    }
    $lines = foreach ($file in ($files | Sort-Object FullName)) {
        $relative = $file.FullName.Substring($Root.Length).TrimStart("\", "/")
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        "{0}`0{1}" -f $relative, $hash
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "")
    } finally {
        $sha.Dispose()
    }
}

function Get-RequiredCommandPath {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "$Name is required; run this helper from an x64 Visual Studio developer shell"
    }
    return $command.Source
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

$cmake = Get-RequiredCommandPath "cmake"
$ninja = Get-RequiredCommandPath "ninja"
$compiler = Get-RequiredCommandPath "cl"
[void](Get-RequiredCommandPath "ctest")

$sourceFingerprintBefore = Get-NativeBridgeSourceFingerprint -Root $sourceDir

# Creating the empty directory ourselves makes the non-reuse check atomic for
# this invocation. It is intentionally retained on any failure for diagnosis.
[void](New-Item -ItemType Directory -Path $buildDirPath -ErrorAction Stop)

$priorVsLang = $env:VSLANG
try {
    # CMake/Ninja parses cl.exe /showIncludes output. Code page 936 previously
    # produced a mojibake msvc_deps_prefix and zero recorded header dependencies.
    $env:VSLANG = "1033"
    Invoke-CheckedCommand -FilePath $cmake -Arguments @(
        "-S", $sourceDir,
        "-B", $buildDirPath,
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=$Configuration"
    )
    $msvcDependencyPrefixMode = Repair-NinjaMsvcDependencyPrefix `
        -BuildRoot $buildDirPath `
        -CompilerPath $compiler
    Invoke-CheckedCommand -FilePath $cmake -Arguments @(
        "--build", $buildDirPath,
        "--parallel"
    )

    foreach ($object in $dependencyObjects) {
        $dependencyOutput = @(& $ninja -C $buildDirPath -t deps $object 2>&1)
        if ($LASTEXITCODE -ne 0) {
            throw "could not inspect Ninja dependencies for $object"
        }
        $dependencyText = $dependencyOutput -join "`n"
        if ($dependencyText -notmatch "#deps\s+[1-9][0-9]*" -or
            $dependencyText -notmatch "ck3_11906\.hpp") {
            throw "Ninja did not record ck3_11906.hpp for $object; refusing this native bridge build"
        }
    }

    if (-not $SkipTests) {
        Invoke-CheckedCommand -FilePath (Get-RequiredCommandPath "ctest") -Arguments @(
            "--test-dir", $buildDirPath,
            "--output-on-failure"
        )
    }
} finally {
    if ($null -eq $priorVsLang) {
        Remove-Item Env:VSLANG -ErrorAction SilentlyContinue
    } else {
        $env:VSLANG = $priorVsLang
    }
}

$sourceFingerprintAfter = Get-NativeBridgeSourceFingerprint -Root $sourceDir
if ($sourceFingerprintAfter -ne $sourceFingerprintBefore) {
    throw "native bridge sources changed during the fresh build; refusing its artifacts"
}

$dllPath = Join-Path $buildDirPath "xar_ck3_bridge.dll"
$injectorPath = Join-Path $buildDirPath "xar_ck3_bridge_injector.exe"
foreach ($artifact in @($dllPath, $injectorPath)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "fresh native bridge artifact is missing: $artifact"
    }
}

[ordered]@{
    status = "ready"
    build_dir = $buildDirPath
    source_fingerprint_sha256 = $sourceFingerprintAfter
    dll_path = $dllPath
    dll_sha256 = (Get-FileHash -LiteralPath $dllPath -Algorithm SHA256).Hash
    injector_path = $injectorPath
    injector_sha256 = (Get-FileHash -LiteralPath $injectorPath -Algorithm SHA256).Hash
    tests_ran = (-not $SkipTests)
    dependency_gate = "ck3_11906.hpp-recorded"
    msvc_dependency_prefix_mode = $msvcDependencyPrefixMode
} | ConvertTo-Json -Depth 4
