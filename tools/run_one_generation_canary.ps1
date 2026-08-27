[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$SourceState,
    [string]$TargetState,
    [string]$GameDir,
    [string]$PythonPath,
    [string]$BridgeDll,
    [string]$BridgeInjector,
    [switch]$Execute,
    [switch]$SkipRepositoryCheck,
    [int]$MaxTurns = 20,
    [double]$TimeoutSeconds = 21600,
    [double]$ReadinessTimeoutSeconds = 300,
    [int]$CheckpointEveryAdvances = 3,
    [string]$ExpectedRepoRevision = "480f287489eb91efd65f94ec07bc39f681960bd0",
    [long]$ExpectedCheckpointSize = 67118175,
    [string]$ExpectedCheckpointSha256 = "12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D",
    [string]$ExpectedDriverStateSha256 = "3C3BBFECDC6941B17B1CC946CEDA1011ABF3DD673AD511B1BFB764FC20E955A9",
    [string]$ExpectedBridgeDllSha256 = "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF",
    [string]$ExpectedBridgeInjectorSha256 = "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$CanonicalCheckpointSize = 67118175L
$CanonicalRepoRevision = "480f287489eb91efd65f94ec07bc39f681960bd0"
$CanonicalCheckpointSha256 = "12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D"
$CanonicalDriverStateSha256 = "3C3BBFECDC6941B17B1CC946CEDA1011ABF3DD673AD511B1BFB764FC20E955A9"
$CanonicalBridgeDllSha256 = "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF"
$CanonicalBridgeInjectorSha256 = "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF"
$ExpectedPipe = "\\.\pipe\xar_ck3_restore_exact2_7aff1d0"
$ExpectedCharacterId = 29829
$ExpectedEpisodeRunId = "native-29829-ee172aa720db"
$ExpectedDateRaw = 53177976
$ExpectedHistoryIndex = 402
$ExpectedInteractiveUser = "xenoa"
$ExpectedDesktop = "WinSta0\Default"

function Resolve-FullPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$BasePath = (Get-Location).Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BasePath $Path))
}

function Test-EqualOrDescendantPath {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $candidatePath = [System.IO.Path]::GetFullPath($Candidate).TrimEnd("\", "/")
    $rootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd("\", "/")
    if ($candidatePath.Equals($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $candidatePath.StartsWith(
        $rootPath + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Assert-HexSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ($Value -notmatch "^[0-9A-Fa-f]{64}$") {
        throw "$Label must be a 64-character SHA-256"
    }
}

function Assert-FileIdentity {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [long]$ExpectedSize = -1,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
    $item = Get-Item -LiteralPath $Path
    if ($ExpectedSize -ge 0 -and $item.Length -ne $ExpectedSize) {
        throw "$Label size differs: $($item.Length) != $ExpectedSize ($Path)"
    }
    $actualSha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actualSha256 -ne $ExpectedSha256.ToUpperInvariant()) {
        throw "$Label SHA-256 differs: $actualSha256 != $($ExpectedSha256.ToUpperInvariant()) ($Path)"
    }
    return [ordered]@{
        path = [System.IO.Path]::GetFullPath($Path)
        size = [long]$item.Length
        sha256 = $actualSha256
    }
}

function Read-DriverAnchor {
    param(
        [Parameter(Mandatory = $true)][string]$StateRoot,
        [Parameter(Mandatory = $true)][string]$CheckpointSha256,
        [Parameter(Mandatory = $true)][long]$CheckpointSize,
        [Parameter(Mandatory = $true)][string]$DriverStateSha256
    )

    $driverPath = Join-Path $StateRoot "native-session\driver-state.json"
    if (-not (Test-Path -LiteralPath $driverPath -PathType Leaf)) {
        throw "driver state is missing: $driverPath"
    }
    try {
        $driver = Get-Content -LiteralPath $driverPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "driver state is not valid JSON: $driverPath`: $($_.Exception.Message)"
    }
    $checkpoint = $driver.last_checkpoint
    $history = @($driver.command_history)
    if ($driver.format_version -ne 2 -or
        $driver.pipe_name -ne $ExpectedPipe -or
        $driver.episode_character_id -ne $ExpectedCharacterId -or
        $driver.episode_run_id -ne $ExpectedEpisodeRunId -or
        $null -eq $checkpoint -or
        $checkpoint.status -ne "saved" -or
        $checkpoint.name -ne "xar_checkpoint.ck3" -or
        [long]$checkpoint.size -ne $CheckpointSize -or
        ([string]$checkpoint.sha256).ToUpperInvariant() -ne $CheckpointSha256.ToUpperInvariant() -or
        $checkpoint.date_raw -ne $ExpectedDateRaw -or
        $checkpoint.history_index -ne $ExpectedHistoryIndex -or
        $checkpoint.episode_character_id -ne $ExpectedCharacterId -or
        $checkpoint.episode_run_id -ne $ExpectedEpisodeRunId -or
        $history.Count -lt $ExpectedHistoryIndex) {
        throw "driver state does not match the exact production6b checkpoint anchor: $driverPath"
    }
    $anchor = $history[$ExpectedHistoryIndex - 1]
    $saved = $anchor.result.checkpoint
    if ($anchor.index -ne $ExpectedHistoryIndex -or
        $anchor.command -ne "save-checkpoint" -or
        $anchor.ok -ne $true -or
        $null -eq $saved -or
        [long]$saved.size -ne $CheckpointSize -or
        ([string]$saved.sha256).ToUpperInvariant() -ne $CheckpointSha256.ToUpperInvariant() -or
        $saved.date_raw -ne $ExpectedDateRaw) {
        throw "driver history index $ExpectedHistoryIndex is not the matching save-checkpoint anchor: $driverPath"
    }
    $driverIdentity = Assert-FileIdentity `
        -Path $driverPath `
        -ExpectedSha256 $DriverStateSha256 `
        -Label "driver state"
    return [ordered]@{
        path = $driverIdentity.path
        size = $driverIdentity.size
        sha256 = $driverIdentity.sha256
        format_version = 2
        pipe = $ExpectedPipe
        episode_character_id = $ExpectedCharacterId
        episode_run_id = $ExpectedEpisodeRunId
        date_raw = $ExpectedDateRaw
        history_index = $ExpectedHistoryIndex
    }
}

function Get-DesktopIdentity {
    if (-not ("Xar.OneGenerationCanaryDesktop" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Xar {
    public static class OneGenerationCanaryDesktop {
        [DllImport("kernel32.dll")]
        private static extern uint GetCurrentThreadId();

        [DllImport("user32.dll")]
        private static extern IntPtr GetProcessWindowStation();

        [DllImport("user32.dll")]
        private static extern IntPtr GetThreadDesktop(uint threadId);

        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool GetUserObjectInformation(
            IntPtr handle,
            int index,
            StringBuilder value,
            int length,
            out int needed
        );

        private static string Name(IntPtr handle) {
            var value = new StringBuilder(512);
            int needed;
            if (!GetUserObjectInformation(handle, 2, value, value.Capacity * 2, out needed)) {
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            }
            return value.ToString();
        }

        public static string Current() {
            return Name(GetProcessWindowStation()) + "\\" + Name(GetThreadDesktop(GetCurrentThreadId()));
        }
    }
}
"@
    }
    return [Xar.OneGenerationCanaryDesktop]::Current()
}

function Invoke-JsonCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][int[]]$AllowedExitCodes,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $output = @(& $FilePath @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { [string]$_ }) -join "`n"
    if ($AllowedExitCodes -notcontains $exitCode) {
        throw "$Label exited $exitCode`: $text"
    }
    try {
        $payload = $text | ConvertFrom-Json
    } catch {
        throw "$Label did not emit one JSON document (exit $exitCode): $text"
    }
    return [ordered]@{
        exit_code = $exitCode
        payload = $payload
    }
}

function Get-JsonProperty {
    param(
        [object]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function ConvertTo-StableJson {
    param([object]$Object)

    return ($Object | ConvertTo-Json -Depth 100 -Compress)
}

function Test-ArtifactBinding {
    param(
        [Parameter(Mandatory = $true)][string]$RunDir,
        [object]$Entry,
        [Parameter(Mandatory = $true)][string]$ExpectedRelativePath,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $verification = [ordered]@{
        ok = $false
        label = $Label
        expected_relative_path = $ExpectedRelativePath
        path = $null
        size = $null
        sha256 = $null
        error = $null
    }
    try {
        if ($null -eq $Entry) {
            throw "$Label artifact entry is missing"
        }
        $relative = Get-JsonProperty -Object $Entry -Name "path"
        $size = Get-JsonProperty -Object $Entry -Name "size"
        $sha256 = Get-JsonProperty -Object $Entry -Name "sha256"
        if (-not ($relative -is [string]) -or
            [string]::IsNullOrWhiteSpace($relative) -or
            [System.IO.Path]::IsPathRooted($relative) -or
            $relative.Replace("\", "/") -ne $ExpectedRelativePath) {
            throw "$Label artifact path is not the expected relative path"
        }
        if ($size -is [bool] -or -not ($size -is [ValueType]) -or [long]$size -le 0) {
            throw "$Label artifact size is malformed"
        }
        if (-not ($sha256 -is [string]) -or $sha256 -notmatch "^[0-9A-Fa-f]{64}$") {
            throw "$Label artifact SHA-256 is malformed"
        }
        $runRoot = [System.IO.Path]::GetFullPath($RunDir)
        $artifactPath = [System.IO.Path]::GetFullPath((Join-Path $runRoot $relative))
        if (-not (Test-EqualOrDescendantPath -Candidate $artifactPath -Root $runRoot) -or
            $artifactPath.Equals($runRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "$Label artifact escapes the run directory"
        }
        $identity = Assert-FileIdentity `
            -Path $artifactPath `
            -ExpectedSha256 $sha256 `
            -ExpectedSize ([long]$size) `
            -Label "$Label artifact"
        $verification.ok = $true
        $verification.path = $identity.path
        $verification.size = $identity.size
        $verification.sha256 = $identity.sha256
    } catch {
        $verification.error = $_.Exception.Message
    }
    return $verification
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $scriptDir ".."
}
$RepoRoot = Resolve-FullPath -Path $RepoRoot

if ([string]::IsNullOrWhiteSpace($SourceState)) {
    $SourceState = Join-Path $env:TEMP "xar-war-entry-production6b-state"
}
$SourceState = Resolve-FullPath -Path $SourceState

if ([string]::IsNullOrWhiteSpace($TargetState)) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
    $TargetState = Join-Path $env:TEMP ("xar-one-generation-canary-{0}-{1}-state" -f $stamp, $suffix)
}
$TargetState = Resolve-FullPath -Path $TargetState

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    if (-not [string]::IsNullOrWhiteSpace($env:XAR_CK3_GAME_DIR)) {
        $GameDir = $env:XAR_CK3_GAME_DIR
    } else {
        $GameDir = Join-Path $RepoRoot "Crusader Kings III"
    }
}
$GameDir = Resolve-FullPath -Path $GameDir -BasePath $RepoRoot

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    if (-not [string]::IsNullOrWhiteSpace($env:XAR_AUTOPLAYER_PYTHON)) {
        $PythonPath = $env:XAR_AUTOPLAYER_PYTHON
    } else {
        $PythonPath = Join-Path $RepoRoot "tools\.venv\Scripts\python.exe"
    }
}
$PythonPath = Resolve-FullPath -Path $PythonPath -BasePath $RepoRoot

if ([string]::IsNullOrWhiteSpace($BridgeDll)) {
    if (-not [string]::IsNullOrWhiteSpace($env:XAR_CK3_BRIDGE_DLL)) {
        $BridgeDll = $env:XAR_CK3_BRIDGE_DLL
    } else {
        $BridgeDll = Join-Path $RepoRoot "ck3_autonomous_player\native_bridge\.build-event-scopes-a860702-msvc\xar_ck3_bridge.dll"
    }
}
$BridgeDll = Resolve-FullPath -Path $BridgeDll -BasePath $RepoRoot

if ([string]::IsNullOrWhiteSpace($BridgeInjector)) {
    if (-not [string]::IsNullOrWhiteSpace($env:XAR_CK3_BRIDGE_INJECTOR)) {
        $BridgeInjector = $env:XAR_CK3_BRIDGE_INJECTOR
    } else {
        $BridgeInjector = Join-Path $RepoRoot "ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe"
    }
}
$BridgeInjector = Resolve-FullPath -Path $BridgeInjector -BasePath $RepoRoot

foreach ($pair in @(
    @($ExpectedCheckpointSha256, "ExpectedCheckpointSha256"),
    @($ExpectedDriverStateSha256, "ExpectedDriverStateSha256"),
    @($ExpectedBridgeDllSha256, "ExpectedBridgeDllSha256"),
    @($ExpectedBridgeInjectorSha256, "ExpectedBridgeInjectorSha256")
)) {
    Assert-HexSha256 -Value $pair[0] -Label $pair[1]
}
if ($ExpectedRepoRevision -notmatch "^[0-9A-Fa-f]{40}$") {
    throw "ExpectedRepoRevision must be a full 40-character Git revision"
}
if ($MaxTurns -ne 20) {
    throw "this handoff is the exact 20-turn canary; MaxTurns must remain 20"
}
if ($TimeoutSeconds -le 0 -or $ReadinessTimeoutSeconds -le 0 -or $CheckpointEveryAdvances -lt 1) {
    throw "timeouts and checkpoint cadence must be positive"
}
if ($Execute -and (
    $TimeoutSeconds -ne 21600 -or
    $ReadinessTimeoutSeconds -ne 300 -or
    $CheckpointEveryAdvances -ne 3
)) {
    throw "Execute requires the fixed canary bounds: timeout 21600, readiness 300, checkpoint cadence 3"
}
if ($Execute -and $SkipRepositoryCheck) {
    throw "SkipRepositoryCheck is dry-run-only and cannot be combined with Execute"
}
if ($Execute -and (
    $ExpectedRepoRevision.ToLowerInvariant() -ne $CanonicalRepoRevision -or
    $ExpectedCheckpointSize -ne $CanonicalCheckpointSize -or
    $ExpectedCheckpointSha256.ToUpperInvariant() -ne $CanonicalCheckpointSha256 -or
    $ExpectedDriverStateSha256.ToUpperInvariant() -ne $CanonicalDriverStateSha256 -or
    $ExpectedBridgeDllSha256.ToUpperInvariant() -ne $CanonicalBridgeDllSha256 -or
    $ExpectedBridgeInjectorSha256.ToUpperInvariant() -ne $CanonicalBridgeInjectorSha256
)) {
    throw "Execute requires the canonical production6b checkpoint and bridge identities"
}

$agentPath = Join-Path $RepoRoot "ck3_autonomous_player\agent.py"
foreach ($requiredFile in @($agentPath, $PythonPath)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "required file is missing: $requiredFile"
    }
}
if (-not (Test-Path -LiteralPath $GameDir -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $GameDir "binaries\ck3.exe") -PathType Leaf)) {
    throw "CK3 game directory is incomplete: $GameDir"
}
if (-not (Test-Path -LiteralPath $SourceState -PathType Container)) {
    throw "production6b source state is missing: $SourceState"
}
if (Test-Path -LiteralPath $TargetState) {
    throw "fresh canary target already exists; refusing overwrite: $TargetState"
}
$tempRoot = Resolve-FullPath -Path $env:TEMP
if (-not (Test-EqualOrDescendantPath -Candidate $TargetState -Root $tempRoot) -or
    (Resolve-FullPath -Path $TargetState).TrimEnd("\", "/") -eq $tempRoot.TrimEnd("\", "/")) {
    throw "canary target must be a fresh descendant of the current TEMP directory: $TargetState"
}
if ((Test-EqualOrDescendantPath -Candidate $TargetState -Root $SourceState) -or
    (Test-EqualOrDescendantPath -Candidate $SourceState -Root $TargetState)) {
    throw "source and target state paths must not overlap: $SourceState <-> $TargetState"
}
$reparsePoint = Get-ChildItem -LiteralPath $SourceState -Recurse -Force |
    Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 } |
    Select-Object -First 1
if ($null -ne $reparsePoint) {
    throw "source state contains a reparse point and is not safe for an exact tree copy: $($reparsePoint.FullName)"
}

$gitRevision = $null
if (-not $SkipRepositoryCheck) {
    $gitTop = (& git -C $RepoRoot rev-parse --show-toplevel 2>&1 | ForEach-Object { [string]$_ }) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "RepoRoot is not a Git worktree: $RepoRoot`: $gitTop"
    }
    $gitTop = Resolve-FullPath -Path $gitTop.Trim()
    if (-not $gitTop.Equals($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "RepoRoot is not the Git worktree root: $RepoRoot != $gitTop"
    }
    $gitStatus = @(& git -C $RepoRoot status --porcelain=v1 --untracked-files=all 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "could not inspect Git status: $($gitStatus -join "`n")"
    }
    if ($gitStatus.Count -ne 0) {
        throw "final canary source clone is not clean:`n$($gitStatus -join "`n")"
    }
    $gitRevision = ((& git -C $RepoRoot rev-parse HEAD 2>&1) | ForEach-Object { [string]$_ }) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $gitRevision.Trim() -notmatch "^[0-9a-fA-F]{40}$") {
        throw "could not resolve the clean source revision"
    }
    $gitRevision = $gitRevision.Trim().ToLowerInvariant()
    if ($gitRevision -ne $ExpectedRepoRevision.ToLowerInvariant()) {
        throw "clean source revision differs: $gitRevision != $($ExpectedRepoRevision.ToLowerInvariant())"
    }
}

$sourceCheckpointPath = Join-Path $SourceState "profile\save games\xar_checkpoint.ck3"
$sourceCheckpoint = Assert-FileIdentity `
    -Path $sourceCheckpointPath `
    -ExpectedSha256 $ExpectedCheckpointSha256 `
    -ExpectedSize $ExpectedCheckpointSize `
    -Label "production6b checkpoint"
$sourceDriver = Read-DriverAnchor `
    -StateRoot $SourceState `
    -CheckpointSha256 $ExpectedCheckpointSha256 `
    -CheckpointSize $ExpectedCheckpointSize `
    -DriverStateSha256 $ExpectedDriverStateSha256
$dll = Assert-FileIdentity `
    -Path $BridgeDll `
    -ExpectedSha256 $ExpectedBridgeDllSha256 `
    -Label "exact-build bridge DLL"
$injector = Assert-FileIdentity `
    -Path $BridgeInjector `
    -ExpectedSha256 $ExpectedBridgeInjectorSha256 `
    -Label "exact-build bridge injector"

$hostUser = [Environment]::UserName
$desktopIdentity = $null
try {
    $desktopIdentity = Get-DesktopIdentity
} catch {
    $desktopIdentity = "unavailable: $($_.Exception.Message)"
}

$prepareArguments = @(
    $agentPath,
    "--state-dir", $TargetState,
    "--game-dir", $GameDir,
    "--bridge-mode", "disabled",
    "prepare-profile"
)
$verifyArguments = @(
    $agentPath,
    "--state-dir", $TargetState,
    "--game-dir", $GameDir,
    "--bridge-mode", "disabled",
    "verify-profile"
)
$canaryArguments = @(
    $agentPath,
    "--state-dir", $TargetState,
    "--game-dir", $GameDir,
    "--bridge-mode", "native-headless",
    "--bridge-pipe", $ExpectedPipe,
    "--bridge-dll", $BridgeDll,
    "--bridge-injector", $BridgeInjector,
    "native-one-generation",
    "--max-turns", "20",
    "--timeout", ([string]$TimeoutSeconds),
    "--readiness-timeout", ([string]$ReadinessTimeoutSeconds),
    "--checkpoint-every-advances", ([string]$CheckpointEveryAdvances)
)
$plan = [ordered]@{
    format_version = 1
    kind = "ck3_one_generation_20_turn_canary_handoff"
    mode = $(if ($Execute) { "execute" } else { "dry_run" })
    repo_root = $RepoRoot
    git_revision = $gitRevision
    source_state = $SourceState
    target_state = $TargetState
    game_dir = $GameDir
    source_checkpoint = $sourceCheckpoint
    source_driver_state = $sourceDriver
    bridge_dll = $dll
    bridge_injector = $injector
    host_observed = [ordered]@{
        user = $hostUser
        desktop = $desktopIdentity
    }
    execute_host_required = [ordered]@{
        user = $ExpectedInteractiveUser
        desktop = $ExpectedDesktop
    }
    copy_contract = "fresh-target, non-overlapping TEMP descendant, robocopy /E without purge or mirror"
    commands = [ordered]@{
        prepare_profile = @($PythonPath) + $prepareArguments
        verify_profile = @($PythonPath) + $verifyArguments
        native_one_generation = @($PythonPath) + $canaryArguments
    }
    strict_canary_contract = [ordered]@{
        max_turns = 20
        qualified_death_within_bound = "exit 0 / outcome qualified"
        alive_at_bound = "exit 1 / outcome bounded_incomplete (expected canary result)"
        blocker_or_harness_failure = "exit 1 / outcome failed (not expected)"
        helper_exit = "0 only after either native outcome above is structurally verified; native exit remains recorded"
        note = "native-one-generation never promotes a turn bound to GREEN"
    }
    known_out_of_scope_debt = [ordered]@{
        scope = "G2 next-episode startup only; does not block this G1 one-lifetime canary"
        observation = "production6b episode-seed.json points outside the cloned state and the cloned profile has no xar_episode_seed.ck3"
        action = "record only; do not mutate the verified production6b source or synthesize an episode seed"
    }
}

if (-not $Execute) {
    $plan | ConvertTo-Json -Depth 8
    return
}

if (-not $hostUser.Equals($ExpectedInteractiveUser, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Execute requires the normal xenoa token; observed user is $hostUser"
}
if ($desktopIdentity -ne $ExpectedDesktop) {
    throw "Execute requires WinSta0\Default; observed desktop is $desktopIdentity"
}
$runningCk3 = @(Get-Process -Name "ck3" -ErrorAction SilentlyContinue)
if ($runningCk3.Count -ne 0) {
    throw "Execute requires no existing ck3.exe; observed PID(s): $($runningCk3.Id -join ', ')"
}

[void](New-Item -ItemType Directory -Path $TargetState -ErrorAction Stop)
$copyOutput = @(& robocopy $SourceState $TargetState /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /XJ /NFL /NDL /NP 2>&1)
$copyExitCode = $LASTEXITCODE
if ($copyExitCode -ge 8) {
    throw "production6b state copy failed with robocopy exit $copyExitCode`: $($copyOutput -join "`n")"
}

$targetCheckpointPath = Join-Path $TargetState "profile\save games\xar_checkpoint.ck3"
$targetCheckpointBeforePrepare = Assert-FileIdentity `
    -Path $targetCheckpointPath `
    -ExpectedSha256 $ExpectedCheckpointSha256 `
    -ExpectedSize $ExpectedCheckpointSize `
    -Label "copied checkpoint"
$targetDriverBeforePrepare = Read-DriverAnchor `
    -StateRoot $TargetState `
    -CheckpointSha256 $ExpectedCheckpointSha256 `
    -CheckpointSize $ExpectedCheckpointSize `
    -DriverStateSha256 $ExpectedDriverStateSha256
if ($targetDriverBeforePrepare.sha256 -ne $sourceDriver.sha256) {
    throw "copied driver-state bytes differ from production6b source"
}

Push-Location $RepoRoot
try {
    $prepared = Invoke-JsonCommand `
        -FilePath $PythonPath `
        -Arguments $prepareArguments `
        -AllowedExitCodes @(0) `
        -Label "prepare-profile"
    $verified = Invoke-JsonCommand `
        -FilePath $PythonPath `
        -Arguments $verifyArguments `
        -AllowedExitCodes @(0) `
        -Label "verify-profile"

    $targetCheckpointAfterPrepare = Assert-FileIdentity `
        -Path $targetCheckpointPath `
        -ExpectedSha256 $ExpectedCheckpointSha256 `
        -ExpectedSize $ExpectedCheckpointSize `
        -Label "prepared checkpoint"
    $targetDriverAfterPrepare = Read-DriverAnchor `
        -StateRoot $TargetState `
        -CheckpointSha256 $ExpectedCheckpointSha256 `
        -CheckpointSize $ExpectedCheckpointSize `
        -DriverStateSha256 $ExpectedDriverStateSha256
    if ($targetDriverAfterPrepare.sha256 -ne $sourceDriver.sha256) {
        throw "prepare/verify changed the copied production6b driver-state bytes"
    }

    $canary = Invoke-JsonCommand `
        -FilePath $PythonPath `
        -Arguments $canaryArguments `
        -AllowedExitCodes @(0, 1) `
        -Label "native-one-generation"
    $postCanaryCk3 = @(Get-Process -Name "ck3" -ErrorAction SilentlyContinue)
    $postCanaryCk3Pids = @($postCanaryCk3 | ForEach-Object { [int]$_.Id })
} finally {
    Pop-Location
}

$sourceCheckpointAfter = Assert-FileIdentity `
    -Path $sourceCheckpointPath `
    -ExpectedSha256 $ExpectedCheckpointSha256 `
    -ExpectedSize $ExpectedCheckpointSize `
    -Label "production6b source checkpoint after canary"
$sourceDriverAfter = Read-DriverAnchor `
    -StateRoot $SourceState `
    -CheckpointSha256 $ExpectedCheckpointSha256 `
    -CheckpointSize $ExpectedCheckpointSize `
    -DriverStateSha256 $ExpectedDriverStateSha256
if ($sourceDriverAfter.sha256 -ne $sourceDriver.sha256) {
    throw "production6b source driver state changed during the canary"
}

$result = $canary.payload
$persistedReport = $null
$stdoutReportMatchesPersisted = $false
$reportIdentityBound = $false
$newestOneGenerationRun = $null
$expectedReportPath = $null
$runsRoot = [System.IO.Path]::GetFullPath((Join-Path $TargetState "runs"))
$oneGenerationRuns = @(
    Get-ChildItem -LiteralPath $runsRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "-one-generation-" } |
        Sort-Object Name
)
if ($oneGenerationRuns.Count -gt 0) {
    $newestOneGenerationRun = [System.IO.Path]::GetFullPath(
        $oneGenerationRuns[-1].FullName
    )
    $expectedReportPath = [System.IO.Path]::GetFullPath(
        (Join-Path $newestOneGenerationRun "report.json")
    )
}
if ($null -ne $expectedReportPath -and
    (Test-Path -LiteralPath $expectedReportPath -PathType Leaf)) {
    try {
        $persistedReport = Get-Content -LiteralPath $expectedReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $persistedReport = $null
    }
}

$stdoutRunId = Get-JsonProperty -Object $result -Name "run_id"
$stdoutRunDir = Get-JsonProperty -Object $result -Name "run_dir"
$stdoutReportPath = Get-JsonProperty -Object $result -Name "report_path"
$persistedRunId = Get-JsonProperty -Object $persistedReport -Name "run_id"
$persistedRunDir = Get-JsonProperty -Object $persistedReport -Name "run_dir"
$persistedReportPath = Get-JsonProperty -Object $persistedReport -Name "report_path"
if ($null -ne $persistedReport -and
    $null -ne $newestOneGenerationRun -and
    $null -ne $expectedReportPath -and
    (Test-EqualOrDescendantPath -Candidate $newestOneGenerationRun -Root $runsRoot) -and
    -not $newestOneGenerationRun.Equals($runsRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
    (Split-Path -Leaf $newestOneGenerationRun) -eq $stdoutRunId -and
    $persistedRunId -eq $stdoutRunId -and
    $stdoutRunDir -eq $newestOneGenerationRun -and
    $persistedRunDir -eq $newestOneGenerationRun -and
    $stdoutReportPath -eq $expectedReportPath -and
    $persistedReportPath -eq $expectedReportPath) {
    $reportIdentityBound = $true
}
if ($reportIdentityBound) {
    try {
        $stdoutReportMatchesPersisted = (
            (ConvertTo-StableJson -Object $result) -eq
            (ConvertTo-StableJson -Object $persistedReport)
        )
    } catch {
        $stdoutReportMatchesPersisted = $false
    }
}

$artifacts = Get-JsonProperty -Object $persistedReport -Name "artifacts"
$firstBlockerEntry = Get-JsonProperty -Object $artifacts -Name "first_blocker"
$terminalEntry = Get-JsonProperty -Object $artifacts -Name "terminal_settlement"
$firstBlockerArtifact = Test-ArtifactBinding `
    -RunDir $(if ($null -eq $newestOneGenerationRun) { $runsRoot } else { $newestOneGenerationRun }) `
    -Entry $firstBlockerEntry `
    -ExpectedRelativePath "first-blocker.json" `
    -Label "first blocker"
$terminalArtifact = Test-ArtifactBinding `
    -RunDir $(if ($null -eq $newestOneGenerationRun) { $runsRoot } else { $newestOneGenerationRun }) `
    -Entry $terminalEntry `
    -ExpectedRelativePath "terminal-settlement.json" `
    -Label "terminal settlement"
$firstBlockerSidecar = $null
$terminalSidecar = $null
if ($firstBlockerArtifact.ok) {
    try {
        $firstBlockerSidecar = Get-Content -LiteralPath $firstBlockerArtifact.path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $firstBlockerSidecar = $null
    }
}
if ($terminalArtifact.ok) {
    try {
        $terminalSidecar = Get-Content -LiteralPath $terminalArtifact.path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $terminalSidecar = $null
    }
}
$persistedFirstBlocker = Get-JsonProperty -Object $persistedReport -Name "first_blocker"
$persistedTerminal = Get-JsonProperty -Object $persistedReport -Name "terminal"
$firstBlockerSidecarMatches = $false
$terminalSidecarMatches = $false
if ($null -ne $firstBlockerSidecar -and $null -ne $persistedFirstBlocker) {
    $firstBlockerSidecarMatches = (
        (ConvertTo-StableJson -Object $firstBlockerSidecar) -eq
        (ConvertTo-StableJson -Object $persistedFirstBlocker)
    )
}
if ($null -ne $terminalSidecar -and $null -ne $persistedTerminal) {
    $terminalSidecarMatches = (
        (ConvertTo-StableJson -Object $terminalSidecar) -eq
        (ConvertTo-StableJson -Object $persistedTerminal)
    )
}

$qualificationGates = Get-JsonProperty -Object $persistedReport -Name "qualification_gates"
$qualificationGatesAllTrue = $false
$requiredQualificationGates = @(
    "start_alive",
    "fixed_seed_verified",
    "started_at_seed_date",
    "same_episode_binding",
    "visible_gameplay",
    "date_advanced",
    "death_terminal_executed",
    "settlement_matches_episode",
    "no_heir_gameplay",
    "cleanup_proven"
)
if ($null -ne $qualificationGates) {
    $gateNames = @($qualificationGates.PSObject.Properties.Name)
    $falseGates = @(
        $qualificationGates.PSObject.Properties |
            Where-Object {
                -not ($_.Value -is [bool]) -or $_.Value -ne $true
            }
    )
    $missingGates = @(
        $requiredQualificationGates |
            Where-Object { $gateNames -notcontains $_ }
    )
    $qualificationGatesAllTrue = (
        $falseGates.Count -eq 0 -and $missingGates.Count -eq 0
    )
}

$persistedCleanup = Get-JsonProperty -Object $persistedReport -Name "cleanup"
$persistedBounds = Get-JsonProperty -Object $persistedReport -Name "bounds"
$persistedCompletionContract = Get-JsonProperty -Object $persistedReport -Name "completion_contract"
$persistedFinalized = Get-JsonProperty -Object $persistedReport -Name "finalized"
$persistedStatus = Get-JsonProperty -Object $persistedReport -Name "status"
$persistedOutcome = Get-JsonProperty -Object $persistedReport -Name "outcome"
$persistedOk = Get-JsonProperty -Object $persistedReport -Name "ok"
$classification = "capability_or_harness_failure"
$expectedCanaryOutcome = $false
if ($canary.exit_code -eq 0 -and
    $reportIdentityBound -and
    $stdoutReportMatchesPersisted -and
    $persistedFinalized -is [bool] -and
    $persistedFinalized -eq $true -and
    $persistedCompletionContract -eq "one_generation" -and
    $persistedStatus -eq "episode_complete" -and
    $persistedOutcome -eq "qualified" -and
    $persistedOk -is [bool] -and
    $persistedOk -eq $true -and
    (Get-JsonProperty -Object $persistedCleanup -Name "ok") -is [bool] -and
    (Get-JsonProperty -Object $persistedCleanup -Name "ok") -eq $true -and
    (Get-JsonProperty -Object $persistedBounds -Name "requested_turns") -eq 20 -and
    (Get-JsonProperty -Object $persistedBounds -Name "max_wall_seconds") -eq 21600 -and
    (Get-JsonProperty -Object $persistedBounds -Name "readiness_timeout_seconds") -eq 300 -and
    (Get-JsonProperty -Object $persistedBounds -Name "checkpoint_every_eligible_advances") -eq 3 -and
    $qualificationGatesAllTrue -and
    $null -eq $persistedFirstBlocker -and
    $null -eq $firstBlockerEntry -and
    $terminalArtifact.ok -and
    $terminalSidecarMatches -and
    $postCanaryCk3Pids.Count -eq 0) {
    $classification = "qualified_death_within_20_turns"
    $expectedCanaryOutcome = $true
} elseif ($canary.exit_code -eq 1 -and
    $reportIdentityBound -and
    $stdoutReportMatchesPersisted -and
    $persistedFinalized -is [bool] -and
    $persistedFinalized -eq $true -and
    $persistedCompletionContract -eq "one_generation" -and
    $persistedStatus -eq "turn_limit" -and
    $persistedOutcome -eq "bounded_incomplete" -and
    $persistedOk -is [bool] -and
    $persistedOk -eq $false -and
    (Get-JsonProperty -Object $persistedCleanup -Name "ok") -is [bool] -and
    (Get-JsonProperty -Object $persistedCleanup -Name "ok") -eq $true -and
    (Get-JsonProperty -Object $persistedBounds -Name "requested_turns") -eq 20 -and
    (Get-JsonProperty -Object $persistedBounds -Name "max_wall_seconds") -eq 21600 -and
    (Get-JsonProperty -Object $persistedBounds -Name "readiness_timeout_seconds") -eq 300 -and
    (Get-JsonProperty -Object $persistedBounds -Name "checkpoint_every_eligible_advances") -eq 3 -and
    (Get-JsonProperty -Object $persistedFirstBlocker -Name "kind") -eq "run_bound_exhausted" -and
    (Get-JsonProperty -Object $persistedFirstBlocker -Name "status") -eq "turn_limit" -and
    (Get-JsonProperty -Object $persistedFirstBlocker -Name "turn_index") -eq 20 -and
    $firstBlockerArtifact.ok -and
    $firstBlockerSidecarMatches -and
    $null -eq $persistedTerminal -and
    $null -eq $terminalEntry -and
    $postCanaryCk3Pids.Count -eq 0) {
    $classification = "expected_bounded_incomplete"
    $expectedCanaryOutcome = $true
}

$summary = [ordered]@{
    format_version = 1
    kind = "ck3_one_generation_20_turn_canary_handoff_result"
    target_state = $TargetState
    git_revision = $gitRevision
    copy_exit_code = $copyExitCode
    source_unchanged = $true
    prepare_profile = $prepared.payload
    verify_profile = $verified.payload
    canary = [ordered]@{
        exit_code = $canary.exit_code
        status = $persistedStatus
        outcome = $persistedOutcome
        ok = $persistedOk
        classification = $classification
        expected_canary_outcome = $expectedCanaryOutcome
        report_path = $expectedReportPath
        run_dir = $newestOneGenerationRun
        report_identity_bound = $reportIdentityBound
        stdout_report_matches_persisted = $stdoutReportMatchesPersisted
        newest_one_generation_run = $newestOneGenerationRun
        finalized = $persistedFinalized
        completion_contract = $persistedCompletionContract
        cleanup = $persistedCleanup
        qualification_gates_all_true = $qualificationGatesAllTrue
        first_blocker_artifact = $firstBlockerArtifact
        first_blocker_sidecar_matches = $firstBlockerSidecarMatches
        terminal_artifact = $terminalArtifact
        terminal_sidecar_matches = $terminalSidecarMatches
        post_canary_ck3_process_count = $postCanaryCk3Pids.Count
        post_canary_ck3_pids = $postCanaryCk3Pids
        first_blocker = $persistedFirstBlocker
    }
    strict_exit_note = "exit 1 with bounded_incomplete is expected for a living ruler at the 20-turn bound; it is intentionally not GREEN"
}
$summary | ConvertTo-Json -Depth 12

if ($expectedCanaryOutcome) {
    exit 0
}
exit 1
