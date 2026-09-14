# Military-preparation live profile companion

Status: `static-ready`; no new CK3 run is claimed by this document.

R685 proved that the private native probe can reach a stable paused session and
publish one result.  The result was `unavailable`, while the fresh managed
profile enabled only `mod/xar_autoplayer.mod`.  That production projection does
not contain
`common/script_values/xar_mcp_military_preparation_summary_v1.txt`; the five
private wrappers live in repository `ck3_autonomous_player/mod_bridge`.
Therefore the profile composition guaranteed a definition-gate failure once
the probe evaluated the wrappers.

The shared repair is
[`companion_profile.py`](../../ck3_autonomous_player/src/xar_autoplayer/companion_profile.py).
It starts from a successfully verified production-only profile, copies only the
loadable `descriptor.mod`, `common`, and `gui` trees into
`profile/mod-content/xar-mcp-bridge`, writes a profile-local absolute outer
descriptor, and enables the companion after the production mod.  It also
installs the repository no-op inbox so the companion GUI poll has a valid
target.  The release projection and both repository descriptors remain
byte-unchanged.

Before CK3 ownership, `verify_mod_bridge_companion` requires all of the
following:

- the enabled playset is exactly production plus the one companion;
- the companion target stays inside the disposable profile;
- its loadable tree is byte-identical to repository `mod_bridge`;
- the production projection has the same tree hash recorded before staging;
- each of the five military wrapper keys appears exactly once with its frozen
  expression.

The resulting receipt is `profile/xar-mod-bridge-companion.json`.  This is an
explicit disposable two-mod profile, so its live runner passes
`verify_prepared_profile=False` only after the dedicated companion preflight is
GREEN.  That flag does not waive verification; it prevents the normal
production-singleton verifier from rejecting the deliberately different
fixture composition.

The canonical next-run entry is
[`run_military_preparation_summary_private_probe_live.py`](../../ck3_autonomous_player/native_bridge/research/run_military_preparation_summary_private_probe_live.py).
It performs one paused, zero-UI, zero-gameplay-action heartbeat and stops.  As
soon as `result_published=true`, it writes the complete diagnostics, probe, and
result to `raw-probe.json` before checking `status`, `failure_flags`, or
`observation_ready`.  A RED therefore retains the exact native failure flags;
R685's lost raw-result gap cannot recur.

## Runtime and direct entry

Do not invoke an artifact-relative `tools/.venv` guess and do not silently fall
back to whichever `py` or `python` is on `PATH`.  The standard-library-only
bootstrap is
[`run_g2_military_preparation_probe.py`](../../tools/run_g2_military_preparation_probe.py).
It selects, in order, an explicit `--python`, `XAR_PYTHON`, a
`--workspace-root` / `XAR_WORKSPACE_ROOT` project runtime, or the checkout's own
`tools/.venv`.  If none exists, or required runtime distributions are missing,
it writes a prelaunch RED and starts no CK3 process.

The bootstrap is a direct Python entry and does not depend on legacy shell script
execution policy.  A portable invocation shape is:

```text
<stdlib-python> tools/run_g2_military_preparation_probe.py \
  --workspace-root <workspace-root> \
  --runtime-preflight-output <artifact>/runtime-preflight.json \
  -- <live-runner arguments>
```

`<workspace-root>` is an operator-provided path containing
`tools/.venv/Scripts/python.exe`; no account name, drive letter, or CK3 round is
embedded in the implementation.  The next live run remains a new round and may
claim `production-live primitive` only if `raw-probe.json` records
`status=available`, `failure_flags=0`, and `observation_ready=true` and cleanup
is GREEN.  This package changes no public MCP/schema and requires no
`open_kaishek` adaptation.
