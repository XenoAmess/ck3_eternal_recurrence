[CmdletBinding()]
param(
    [string]$Manifest = "Z:\ck3_mod_rewrite\artifacts\migrations\2026-09-30\pre-update\cleanup-candidates.json",
    [string]$Result = "Z:\ck3_mod_rewrite\artifacts\migrations\2026-09-30\pre-update\cleanup-result.json",
    [string]$AdminScript = "Z:\ck3_mod_rewrite\tools\cleanup_ck3_admin_20260930.ps1"
)

$ErrorActionPreference = "Stop"
$workspaceRoot = [IO.Path]::GetFullPath("Z:\ck3_mod_rewrite").TrimEnd('\')
$archiveRoot = Join-Path $workspaceRoot "artifacts\migrations\2026-09-30\pre-update"
if (-not (Test-Path -LiteralPath (Join-Path $archiveRoot "retained-build-files.json"))) {
    throw "Retained build products must be archived before cleanup."
}
$candidates = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$removed = [Collections.Generic.List[object]]::new()
$failed = [Collections.Generic.List[object]]::new()
foreach ($entry in $candidates) {
    $target = [IO.Path]::GetFullPath([string]$entry.path)
    if (-not $target.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $target.StartsWith($archiveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target is outside the cleanup workspace: $target"
    }
    try {
        if (Test-Path -LiteralPath $target) {
            $item = Get-Item -LiteralPath $target -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Retain linked directory: $target"
            }
            Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
        }
        $removed.Add($entry)
    } catch {
        $failed.Add([pscustomobject]@{ path=$target; reason=$entry.reason; error=$_.Exception.Message })
    }
}
$payload = [pscustomobject]@{
    completed_at_utc=[DateTime]::UtcNow.ToString("o")
    removed_count=$removed.Count
    removed_known_bytes=($removed | Measure-Object -Property bytes -Sum).Sum
    removed=@($removed.ToArray())
    failed=@($failed.ToArray())
}
$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Result -Encoding UTF8

$lines = [Collections.Generic.List[string]]::new()
$lines.Add('# Run in an Administrator PowerShell. Only the listed failed cleanup targets are removed.')
$lines.Add('$ErrorActionPreference = "Stop"')
$lines.Add('$workspaceRoot = ''Z:\ck3_mod_rewrite''')
$lines.Add('$targets = @(')
foreach ($entry in $failed) {
    $literal = ([string]$entry.path).Replace("'", "''")
    $lines.Add("    '$literal'")
}
$lines.Add(')')
$lines.Add('foreach ($target in $targets) {')
$lines.Add('    $absolute = [IO.Path]::GetFullPath($target)')
$lines.Add('    if (-not $absolute.StartsWith($workspaceRoot + ''\'', [StringComparison]::OrdinalIgnoreCase)) { throw "Unexpected target: $absolute" }')
$lines.Add('    try {')
$lines.Add('        if (Test-Path -LiteralPath $absolute -ErrorAction Stop) {')
$lines.Add('            Write-Host "Removing $absolute"')
$lines.Add('            Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop')
$lines.Add('        }')
$lines.Add('    } catch {')
$lines.Add('        # These exact directories already produced access-denied errors.')
$lines.Add('        # Repair their ACL only if elevated removal still fails.')
$lines.Add('        & takeown.exe /F $absolute /A /R /D Y | Out-Host')
$lines.Add('        & icacls.exe $absolute /reset /T /C /Q | Out-Host')
$lines.Add('        & icacls.exe $absolute /grant:r ''*S-1-5-32-544:(OI)(CI)F'' /T /C /Q | Out-Host')
$lines.Add('        Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop')
$lines.Add('    }')
$lines.Add('}')
$lines.Add('Write-Host "Listed cleanup targets processed."')
[IO.File]::WriteAllLines($AdminScript, $lines.ToArray(), [Text.UTF8Encoding]::new($true))
[pscustomobject]@{
    removed_count=$removed.Count
    removed_known_bytes=$payload.removed_known_bytes
    failed_count=$failed.Count
    admin_script=$AdminScript
} | ConvertTo-Json
