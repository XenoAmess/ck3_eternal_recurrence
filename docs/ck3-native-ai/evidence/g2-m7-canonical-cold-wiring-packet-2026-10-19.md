machine_id: xenoamess-full-tower-eb9d2c1186
observed_at_utc: 2026-10-19T16:31:45.137284+00:00

This is a source integration packet for a future normal maintenance attempt.
It is not deployed to C16/d804, Native29, or the existing Native freeze. The
[source qualification](g2-m7-canonical-source-chain-qualification-2026-10-19.json)
records the actual owned observations and exact source pins. This document does
not report production adoption; the outer controlled entries still must call
the adapters below at their original creation and factory sites.

Use `tools/g2_saved_campaign/canonical_native_provider_chain_v1.py`; every new
entry is default OFF. Freeze the actual SDK, creator tools and all three entry
scripts first. Provide their real absolute paths and SHA values as
`entry_source_pins`; the producer checks bytes again before every spawn. The
creator digest also covers the actual creator, MCP binding and retained-process
helper. These source pins alone cannot authorize a provider.

The accepted [seven-hunk plan](g2-m7-canonical-preload-origin-promotion-plan-2026-10-19.json)
locates the historical real call sites: `root_native29_supervisor_c11.py:448`,
`launch_sdk_p37c15_owner.py:50`, `root_p37c15_sdk_queue.py:3524-3525`, and
`root_p37c15_mcp_entry.py:97-102`. These are source locators, not claims that
those closed generated scripts have adopted this package. Future controlled
entries must preserve their original behavior while using the adapters here.

The canonical supervisor must actually create SDKowner. An independently
started owner cannot import the old source authority after Game launch. Keep
the `CanonicalPreloadFactoryV1` strongly referenced through shutdown, including
unknown cleanup failures. Pass its `pre_native_resume` method to the newly
optional `launch_prepared(..., pre_native_resume=...)` argument, or directly to
`runtime.launch`. That seam runs after actual suspended-process validation and
before either original resume/injection branch. Keep original DLL loading and
Game Job/cleanup ownership. A missing hook preserves the original launch.

```python
factory = CanonicalPreloadFactoryV1(
    facade=actual_enabled_windows_facade,
    machine_id=actual_machine_id,
    expected_dll_sha256=actual_frozen_DLL_sha256,
    entry_source_pins=actual_frozen_entry_pins,
    enabled=private_source_enabled,
)
handle = launch_prepared(
    spec, actual_DLL_path, actual_injector_path,
    pre_native_resume=factory.pre_native_resume if private_source_enabled else None,
)
```

After existing map/recording admission, the same supervisor starts its private
origin handler (`factory.origin.serve`) and creates the exact direct SDKowner
command with `prepare_child_v1` / `spawn_owned_popen_v1`. Keep the returned plan
and its Popen as the original process owner. Do not substitute a descendant PID
for a venv forwarding launcher; use the independently verified direct Python
image and frozen dependency environment. Only finite interpreter flags `-B`,
`-u`, and `-X utf8` are supported before the script. The first script operand
must be the exact frozen entry; `-c`, `-m`, `--` and other interpreter modes
cannot bind an entry merely placed later in argv. The actual returned image
must match the declared direct executable before the child receives an ACK.
Source creation is once-only; errors
retain the exact child and resource references and never start a replacement.
Then `factory.origin.bind_actual_chain(owner_edge)` imports the actual final App
read-handle through the two held parent-child process handles. Unknown rights
reject; no process is reopened from a JSON PID.

Each owned outer entry uses `consume_private_bootstrap_args_v1` before its
original CLI parser, then `receive_child_bootstrap_v1` on the private locations.
The original CLI/MCP API gains no qualification parameter. JSON only locates
inherited resources; actual inherited flags, parent peer, target birth, held
FileID/hash, source closure and ordered creation returns establish the chain.

SDKowner uses the same producer for its exact Queue child. Queue uses
`spawn_owned_mcp_v1` around its original stdio session. That adapter retains the
original stock code objects, Job table, exception propagation and cleanup; it
does not patch a global installed module. Owner and Queue call
`export_actual_child_chain_v1` after retaining the actual child. Hold both
ancestors alive for the provider lifetime. Send an ACK before releasing a
sender's duplicates; keep original gameplay/recording/normal-exit behavior.

At the App's existing original factory, retain the one actual Service as today.
Call `export_actual_child_chain_v1(result, io, control)` without a child, and
`install_received_provider_bootstrap_v1(service, result, enabled=True)` after
the original ordinary App owner exists. The final App opens a fresh dedicated
origin connection. Its kernel server PID must match the held original process;
the original server's client PID must match the final App read-handle obtained
from the real MCP return. No field sets `source_verified=True`.

No extra Game query is required. The first naturally produced optional root
component attempts the existing unique issuer. It verifies the live original
controller source and every original Native peer/module/FileID/generation
guard, then reuses the same DTO/seal. Missing component has zero new IO/RPC.
Eligible exact-birth consumption uses the same held integer FILETIME and fresh
private-origin liveness. Global CIM/microsecond parsing and ledger rules are
unchanged. Private IPC/held waits are real work, not claimed zero OS overhead.

Disconnect, connection replacement and Driver.close clear the DTO/cache before
only owned resources close. Revoke the root before closing its controller
lease; keep unknown releases strongly retained for retry. Original runtime
Game handles, Job handles and Native server pipe remain borrowed by custody.

The existing source-epoch tuple now includes custody, Windows facade, receiver,
origin and origin IO. Freeze those exact SDK bytes with the caller changes.
Preserve original campaign/T0/D0=174 and all gameplay pending/UNKNOWN duties.

Software validation uses four newly owned harmless Python children and one tiny
lease. Kernel birth, creation chain, FileID, peer, revocation and original MCP
Job cleanup are real. Native pre-resume module absence, module identity and hello
observations are explicitly synthetic
to exercise the unique DTO branch, and grant no actual H. Sole runtime still
must prove the actual loaded DLL/provider, Native30 optional component and
first natural same-frame candidate at a normal maintenance boundary. No forced
succession, extra seed matrix, old action replay or current-runtime retrofit.

The four-child observation used the explicitly pinned source before the later
direct-script guard correction. That correction passed pure guard regressions;
the four-child test was not rerun. The qualification record preserves both
source generations and does not transfer the old mechanical run to the new pins.

Record retention follows the project policy: review/consolidate in 180 days;
no permanent raw copies are created by this packet.
