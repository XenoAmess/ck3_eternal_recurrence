# Run in an Administrator PowerShell. Only the listed failed cleanup targets are removed.
$ErrorActionPreference = "Stop"
$workspaceRoot = 'Z:\ck3_mod_rewrite'
$targets = @(
    'Z:\ck3_mod_rewrite\.build-combat-trace-detour-v1b-msvc'
    'Z:\ck3_mod_rewrite\.build-combat-trace-managed-v1-msvc'
    'Z:\ck3_mod_rewrite\.build-startup-consumer-guard-syntax-msvc'
    'Z:\ck3_mod_rewrite\.build-startup-consumer-guard-syntax2-msvc'
    'Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly-msvc'
    'Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly2-msvc'
    'Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly3-msvc'
    'Z:\ck3_mod_rewrite\ck3_autonomous_player\.build-startup-guard-production8-msvc'
    'Z:\ck3_mod_rewrite\ck3_autonomous_player\.build-startup-guard-production8d-msvc'
    'Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\.build-dx11-draw-guard-review-msvc'
    'Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\build-msvc'
    'Z:\ck3_mod_rewrite\_runtime\pytest-portable-normal-1789010595710'
    'Z:\ck3_mod_rewrite\_runtime\pytest-portable-opt-1789010595710'
)
foreach ($target in $targets) {
    $absolute = [IO.Path]::GetFullPath($target)
    if (-not $absolute.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Unexpected target: $absolute" }
    try {
        if (Test-Path -LiteralPath $absolute -ErrorAction Stop) {
            Write-Host "Removing $absolute"
            Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop
        }
    } catch {
        # These exact directories already produced access-denied errors.
        # Repair their ACL only if elevated removal still fails.
        & takeown.exe /F $absolute /A /R /D Y | Out-Host
        & icacls.exe $absolute /reset /T /C /Q | Out-Host
        & icacls.exe $absolute /grant:r '*S-1-5-32-544:(OI)(CI)F' /T /C /Q | Out-Host
        Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop
    }
}
Write-Host "Listed cleanup targets processed."
