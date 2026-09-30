[CmdletBinding()]
param(
    [string]$RecordRoot = "Z:\ck3_mod_rewrite\artifacts\cleanup\2026-09-30-z-root",
    [string]$AdminScript = "Z:\ck3_mod_rewrite\tools\cleanup_z_root_admin_20260930.ps1",
    [ValidateSet('build', 'runtime')][string]$DirectoryKind = 'build'
)

$ErrorActionPreference = "Stop"
$repoRoot = "Z:\ck3_mod_rewrite"
$driveRoot = [IO.Path]::GetFullPath('Z:\')
$materials = Get-Content -LiteralPath (Join-Path $RecordRoot 'retained-materials.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$archived = @{}
foreach ($material in $materials) {
    if ($material.all_member_hashes_verified) { $archived[[IO.Path]::GetFullPath($material.source)] = $true }
}
$builds = Get-Content -LiteralPath (Join-Path $RecordRoot 'build-candidates.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$worktrees = Get-Content -LiteralPath (Join-Path $RecordRoot 'worktree-candidates.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$results = [Collections.Generic.List[object]]::new()
foreach ($kind in @($DirectoryKind, 'worktree')) {
    $candidates = if ($kind -eq 'worktree') { $worktrees } else { $builds }
    foreach ($entry in $candidates) {
        $target = [IO.Path]::GetFullPath([string]$entry.path)
        if ([IO.Path]::GetDirectoryName($target) -ne $driveRoot -or $target -eq $repoRoot) {
            throw "Target is not an approved temporary directory directly under Z:\: $target"
        }
        if (-not $archived.ContainsKey($target)) { throw "Materials not archived: $target" }
        $ok = $false
        $detail = ''
        try {
            foreach ($nested in $entry.nested_worktrees) {
                $nestedTarget = [IO.Path]::GetFullPath([string]$nested.path)
                if (-not $nestedTarget.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) {
                    throw "Nested worktree is outside its approved runtime: $nestedTarget"
                }
                $detail = (& git -c core.longpaths=true -C $repoRoot worktree remove -- $nestedTarget 2>&1 | Out-String)
                if ($LASTEXITCODE -ne 0) { throw $detail }
            }
            if ($kind -eq 'worktree') {
                $detail = (& git -c core.longpaths=true -C $repoRoot worktree remove -- $target 2>&1 | Out-String)
                if ($LASTEXITCODE -ne 0) { throw $detail }
            } elseif (Test-Path -LiteralPath $target -ErrorAction Stop) {
                $item = Get-Item -LiteralPath $target -Force
                if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked directory retained: $target" }
                Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
            }
            $ok = $true
        } catch {
            $detail = $_.Exception.Message
        }
        $results.Add([pscustomobject]@{ kind=$kind; path=$target; head=$entry.head; bytes=$entry.bytes; removed=$ok; detail=$detail })
    }
}
$failed = @($results | Where-Object { -not $_.removed })
$adminTargets = @($failed | Where-Object { $_.detail -match '(?is)access.*denied|permission.*denied|unauthorized|拒绝访问|权限不足' })
$payload = [pscustomobject]@{
    completed_at_utc=[DateTime]::UtcNow.ToString('o')
    removed_count=(@($results | Where-Object removed).Count)
    removed_known_bytes=($results | Where-Object removed | Measure-Object -Property bytes -Sum).Sum
    failed_count=$failed.Count
    results=$results.ToArray()
}
$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $RecordRoot 'cleanup-result.json') -Encoding UTF8

if ($adminTargets.Count -eq 0) {
    [pscustomobject]@{removed_count=$payload.removed_count; removed_known_bytes=$payload.removed_known_bytes; failed_count=$failed.Count; admin_script=$null} | ConvertTo-Json
    return
}

$lines = [Collections.Generic.List[string]]::new()
$lines.Add('# Run in an Administrator PowerShell. These exact targets failed the authorized Z-root cleanup.')
$lines.Add('$ErrorActionPreference = "Stop"')
$lines.Add('$driveRoot = [IO.Path]::GetFullPath(''Z:\'')')
$lines.Add('$targets = @(')
foreach ($entry in $adminTargets) {
    $literal = $entry.path.Replace("'", "''")
    $lines.Add("    @{ kind='$($entry.kind)'; path='$literal' }")
}
$lines.Add(')')
$lines.Add('foreach ($entry in $targets) {')
$lines.Add('    $absolute = [IO.Path]::GetFullPath($entry.path)')
$lines.Add('    if ([IO.Path]::GetDirectoryName($absolute) -ne $driveRoot -or $absolute -eq ''Z:\ck3_mod_rewrite'') { throw "Unexpected target: $absolute" }')
$lines.Add('    try {')
$lines.Add('        if ($entry.kind -eq ''worktree'') {')
$lines.Add('            & git -c core.longpaths=true -C ''Z:\ck3_mod_rewrite'' worktree remove -- $absolute')
$lines.Add('            if ($LASTEXITCODE -ne 0) { throw "Git worktree removal failed: $absolute" }')
$lines.Add('        } elseif (Test-Path -LiteralPath $absolute -ErrorAction Stop) {')
$lines.Add('            Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop')
$lines.Add('        }')
$lines.Add('    } catch {')
$lines.Add('        & takeown.exe /F $absolute /A /R /D Y | Out-Host')
$lines.Add('        & icacls.exe $absolute /reset /T /C /Q | Out-Host')
$lines.Add('        & icacls.exe $absolute /grant:r ''*S-1-5-32-544:(OI)(CI)F'' /T /C /Q | Out-Host')
$lines.Add('        if ($entry.kind -eq ''worktree'') {')
$lines.Add('            & git -c core.longpaths=true -C ''Z:\ck3_mod_rewrite'' worktree remove -- $absolute')
$lines.Add('            if ($LASTEXITCODE -ne 0) { throw "Git worktree removal failed: $absolute" }')
$lines.Add('        } else {')
$lines.Add('            Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop')
$lines.Add('        }')
$lines.Add('    }')
$lines.Add('}')
$lines.Add('Write-Host "Listed Z-root cleanup targets processed."')
[IO.File]::WriteAllLines($AdminScript, $lines.ToArray(), [Text.UTF8Encoding]::new($true))
[pscustomobject]@{removed_count=$payload.removed_count; removed_known_bytes=$payload.removed_known_bytes; failed_count=$failed.Count; admin_script=$AdminScript} | ConvertTo-Json
