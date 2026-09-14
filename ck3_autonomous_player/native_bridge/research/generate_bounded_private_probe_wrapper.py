"""Generate a PowerShell launcher that preserves a manifest's pipe verbatim."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PIPE_PREFIX = "\\\\.\\pipe\\"
_SAFE_PIPE_SUFFIX = re.compile(r"[A-Za-z0-9._-]+\Z")
_ROUND = re.compile(r"R[1-9][0-9]*\Z")
_SHA256 = re.compile(r"[0-9A-Fa-f]{64}\Z")
_REVISION = re.compile(r"[0-9A-Fa-f]{40}\Z")


def validate_named_pipe(value: object) -> str:
    if not isinstance(value, str) or not value.startswith(PIPE_PREFIX):
        raise ValueError(f"pipe name must start with {PIPE_PREFIX!r}")
    suffix = value[len(PIPE_PREFIX) :]
    if not _SAFE_PIPE_SUFFIX.fullmatch(suffix):
        raise ValueError("pipe suffix must contain only ASCII letters, digits, ._- ")
    return value


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _relative(value: str, name: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must stay below the candidate root")
    return str(path).replace("/", "\\")


def _required_match(pattern: re.Pattern[str], value: str, name: str) -> str:
    if not pattern.fullmatch(value):
        raise ValueError(f"invalid {name}: {value!r}")
    return value


def render_wrapper(
    *,
    manifest_relative: str,
    bootstrap_relative: str,
    save_relative: str,
    dll_relative: str,
    injector_relative: str,
    save_name: str,
    expected_save_sha256: str,
    expected_dll_sha256: str,
    expected_injector_sha256: str,
    expected_game_exe_sha256: str,
    expected_character_id: int,
    old_round: str,
    new_round: str,
    candidate_revision: str,
    publish_timeout: int,
) -> str:
    manifest_relative = _relative(manifest_relative, "manifest path")
    bootstrap_relative = _relative(bootstrap_relative, "bootstrap path")
    save_relative = _relative(save_relative, "save path")
    dll_relative = _relative(dll_relative, "DLL path")
    injector_relative = _relative(injector_relative, "injector path")
    for name, value in (
        ("save SHA-256", expected_save_sha256),
        ("DLL SHA-256", expected_dll_sha256),
        ("injector SHA-256", expected_injector_sha256),
        ("game EXE SHA-256", expected_game_exe_sha256),
    ):
        _required_match(_SHA256, value, name)
    _required_match(_ROUND, old_round, "old round")
    _required_match(_ROUND, new_round, "new round")
    _required_match(_REVISION, candidate_revision, "candidate revision")
    if expected_character_id <= 0 or publish_timeout <= 0:
        raise ValueError("character id and publish timeout must be positive")

    replacements = {
        "@@MANIFEST@@": _ps_single_quote(manifest_relative),
        "@@BOOTSTRAP@@": _ps_single_quote(bootstrap_relative),
        "@@SAVE@@": _ps_single_quote(save_relative),
        "@@DLL@@": _ps_single_quote(dll_relative),
        "@@INJECTOR@@": _ps_single_quote(injector_relative),
        "@@SAVE_NAME@@": _ps_single_quote(save_name),
        "@@SAVE_SHA@@": _ps_single_quote(expected_save_sha256.upper()),
        "@@DLL_SHA@@": _ps_single_quote(expected_dll_sha256.upper()),
        "@@INJECTOR_SHA@@": _ps_single_quote(expected_injector_sha256.upper()),
        "@@EXE_SHA@@": _ps_single_quote(expected_game_exe_sha256.upper()),
        "@@CHARACTER@@": str(expected_character_id),
        "@@OLD_ROUND@@": _ps_single_quote(old_round),
        "@@NEW_ROUND@@": _ps_single_quote(new_round),
        "@@REVISION@@": _ps_single_quote(candidate_revision.lower()),
        "@@TIMEOUT@@": str(publish_timeout),
    }
    template = r'''param(
  [Parameter(Mandatory=$true)][string]$Python,
  [Parameter(Mandatory=$true)][string]$GameDir,
  [Parameter(Mandatory=$true)][string]$ArtifactDir,
  [Parameter(Mandatory=$true)][string]$StateDir,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Join-Path $root @@MANIFEST@@
$bootstrap = Join-Path $root @@BOOTSTRAP@@
$save = Join-Path $root @@SAVE@@
$dll = Join-Path $root @@DLL@@
$injector = Join-Path $root @@INJECTOR@@
$gameExe = Join-Path $GameDir "binaries\ck3.exe"
$manifestObject = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
$manifestPipe = [string]$manifestObject.next_live.unique_pipe
$requiredPrefix = "\\.\pipe\"
if (-not $manifestPipe.StartsWith($requiredPrefix, [StringComparison]::Ordinal)) {
  throw "manifest pipe does not start with the canonical \\\\.\\pipe\\ prefix"
}
$pipeSuffix = $manifestPipe.Substring($requiredPrefix.Length)
if ($pipeSuffix -notmatch '^[A-Za-z0-9._-]+$') {
  throw "manifest pipe has a non-canonical suffix"
}
foreach ($inputPath in @($manifest, $bootstrap, $save, $dll, $injector, $gameExe)) {
  if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
    throw "required input is missing: $inputPath"
  }
}
function Require-Sha256([string]$Path, [string]$Expected) {
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
  if (-not [string]::Equals($actual, $Expected, [StringComparison]::OrdinalIgnoreCase)) {
    throw "SHA-256 mismatch: $Path"
  }
}
Require-Sha256 $save @@SAVE_SHA@@
Require-Sha256 $dll @@DLL_SHA@@
Require-Sha256 $injector @@INJECTOR_SHA@@
Require-Sha256 $gameExe @@EXE_SHA@@
$manifestSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash
$runnerArguments = @(
  '--artifact-dir', $ArtifactDir,
  '--state-dir', $StateDir,
  '--game-dir', $GameDir,
  '--source-save', $save,
  '--save-name', @@SAVE_NAME@@,
  '--expected-save-sha256', @@SAVE_SHA@@,
  '--candidate-manifest', $manifest,
  '--expected-candidate-manifest-sha256', $manifestSha,
  '--bridge-dll', $dll,
  '--expected-bridge-dll-sha256', @@DLL_SHA@@,
  '--bridge-injector', $injector,
  '--expected-bridge-injector-sha256', @@INJECTOR_SHA@@,
  '--expected-game-exe-sha256', @@EXE_SHA@@,
  '--expected-character-id', '@@CHARACTER@@',
  '--pipe', $manifestPipe,
  '--old-round', @@OLD_ROUND@@,
  '--new-round', @@NEW_ROUND@@,
  '--candidate-revision', @@REVISION@@,
  '--publish-timeout', '@@TIMEOUT@@'
)
$pipeIndex = [Array]::IndexOf($runnerArguments, '--pipe')
$argumentPipe = [string]$runnerArguments[$pipeIndex + 1]
if (-not [string]::Equals($argumentPipe, $manifestPipe, [StringComparison]::Ordinal)) {
  throw "runner pipe argument differs from candidate manifest"
}
if ($DryRun) {
  [ordered]@{
    schema = 'xar.ck3.bounded_private_probe_wrapper_dry_run_v1'
    status = 'green'
    ck3_launched = $false
    manifest_pipe = $manifestPipe
    argument_pipe = $argumentPipe
    argument_pipe_utf16 = @($argumentPipe.ToCharArray() | ForEach-Object { [int][char]$_ })
    manifest_sha256 = $manifestSha
  } | ConvertTo-Json -Depth 5
  exit 0
}
& $Python $bootstrap --python $Python --runtime-preflight-output (Join-Path $ArtifactDir "runtime-preflight.json") -- @runnerArguments
exit $LASTEXITCODE
'''
    for needle, replacement in replacements.items():
        template = template.replace(needle, replacement)
    if "@@" in template:
        raise RuntimeError("unresolved wrapper template token")
    return template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--manifest-relative", default="candidate-manifest.json")
    parser.add_argument("--output-relative", default="run-bounded-private-probe.ps1")
    parser.add_argument("--bootstrap-relative", required=True)
    parser.add_argument("--save-relative", required=True)
    parser.add_argument("--dll-relative", required=True)
    parser.add_argument("--injector-relative", required=True)
    parser.add_argument("--save-name", required=True)
    parser.add_argument("--expected-save-sha256", required=True)
    parser.add_argument("--expected-dll-sha256", required=True)
    parser.add_argument("--expected-injector-sha256", required=True)
    parser.add_argument("--expected-game-exe-sha256", required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--old-round", required=True)
    parser.add_argument("--new-round", required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--publish-timeout", type=int, required=True)
    args = parser.parse_args(argv)

    root = args.candidate_root.resolve()
    manifest_relative = _relative(args.manifest_relative, "manifest path")
    output_relative = _relative(args.output_relative, "output path")
    manifest = json.loads((root / manifest_relative).read_text(encoding="utf-8-sig"))
    validate_named_pipe(manifest.get("next_live", {}).get("unique_pipe"))
    output = root / output_relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_wrapper(
            manifest_relative=manifest_relative,
            bootstrap_relative=args.bootstrap_relative,
            save_relative=args.save_relative,
            dll_relative=args.dll_relative,
            injector_relative=args.injector_relative,
            save_name=args.save_name,
            expected_save_sha256=args.expected_save_sha256,
            expected_dll_sha256=args.expected_dll_sha256,
            expected_injector_sha256=args.expected_injector_sha256,
            expected_game_exe_sha256=args.expected_game_exe_sha256,
            expected_character_id=args.expected_character_id,
            old_round=args.old_round,
            new_round=args.new_round,
            candidate_revision=args.candidate_revision,
            publish_timeout=args.publish_timeout,
        ),
        encoding="utf-8-sig",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
