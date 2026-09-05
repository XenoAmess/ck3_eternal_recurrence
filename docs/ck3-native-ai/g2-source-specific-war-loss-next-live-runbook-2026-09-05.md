# G2 source-specific war-loss next-live runbook

Status: **same-lifecycle continuation and deterministic outer ownership
static-ready / no launch / concrete live adapter still pending**.

This runbook is pinned to root commit
`523432aec7846d0da833c5a351faad743fa23d2d`. It prepares the next exclusive
Raiktor source-attribution capture without launching or attaching to CK3. It
does not change the shared bridge DLL or the standalone C++ observer.

## Exact no-launch command and evidence

Run from
`Z:\ck3_mod_rewrite\_root-promo-split-20260902` with an absent output path:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B `
  "ck3_autonomous_player\native_bridge\research\prepare_raiktor_source_specific_war_loss_capture.py" `
  --contract "ck3_autonomous_player\native_bridge\research\fixtures\raiktor_source_specific_war_loss_attribution_v1_contract.json" `
  --output "Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-specific-war-loss-provider-523432a-20260905\runbook-preflight-r1.json"
```

The command was run once without CK3. Result:

- status `GREEN_STATIC_SOURCE_ATTRIBUTION_PROVIDER`;
- output size `3995` bytes;
- output SHA-256
  `FE3CDDF93E07B0028ED40BF472F55C89589CF497B2395DC587806ED4C913EB4B`;
- contract SHA-256
  `1633808E42C324EF6C282481040B905DAF7FE9B0147F7072382919CA5064F9CE`;
- `exact_build_abi_verified=true`;
- `standalone_default_off_target_ready=true`;
- `capture_supplied=false`, so all live/comparison readiness remains false.

Frozen input SHA-256 values are:

| Input | SHA-256 |
| --- | --- |
| CK3 `1.19.0.6` executable | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| standalone capture executable | `B8328D5C0B52AF667BB71D2BBE660C803BF46EC0A7549A514083B7DBB8BA5A72` |
| `spawn_army` ABI | `C81963E32264CF2B0B09353A8EA25CA0A4035B43B13C9E5C36F050E1BA346AF0` |
| ABI verifier | `A6FEF375185074F5CAC107334DFCED17083FE75B873CF0A8EA27D3A4F5CCAC72` |
| private observer source | `A84601C5BB6927DEF52DF6B27E8602B8C2CAC0C6475A9F1A75B30085433848D8` |
| historical capture manifest | `0D7E4B948F6D6600A6D4412FADAA328728ED451B01330E652548995CF2B9BDAD` |
| native CMake source | `0F871589014C9FE3F0D93AA8072AD830A2AB10D9BCAD64FE5F9138AD5FA6063E` |
| typed provider | `F3204BA33885F12443493B4E0B8FE779C233E4B45047FA46C66079A65D75942A` |
| no-launch preflight | `6286921CF0782FE47EFFEC911BCD93697FF6F77BA99CD815784E957DD0A80D9E` |

The capture executable self-test must remain exactly:

```text
PASS: private=1 action_arm=1 loaded_nodes=6 exact_war_id=1 public_abi=0 readiness=0
```

## Why there is no legal exclusive-live command yet

Do **not** invoke
`run_raiktor_war_bound_private_capture_v1.py` unchanged. Its source SHA-256 is
`53E6086EEACB6ABF4B54D2C7186C38E6212237C247A34E30EC442FB544A0BF56`,
but it hard-codes the unavailable older capture executable SHA-256
`E658470CF7DFC65334E791F1DE301A51FA787916D443AD3BE4C0FCAAFBC3AB72`.
It therefore cannot accept the frozen `B832...A5A72` candidate.

Even if that hash were refreshed, the runner always kills its CK3 process in
`finally` after the six executions. The existing cleanup/expiry runner starts
a different CK3 process from a cold checkpoint. Those two runners therefore
cannot prove a same-PID, same-generation, same-episode chain. Running them in
sequence would create two unrelated live artifacts and must not set
`source_specific_loss_ready` or `comparison_input_ready`.

The minimum Python continuation now exists as
`run_g2_source_specific_war_loss_lifecycle.py`, with its frozen no-launch
manifest and focused deterministic tests. It consumes the already connected
driver from the same capture PID, joins all three exact generation sets,
creates the source-bound retention ticket, and reuses the existing
one-surrender cleanup/expiry continuation. No C++ or DLL change was required.

The deterministic outer-owner composition now exists as
`run_g2_source_specific_war_loss_outer_owner.py`. It requires one exclusive
slot and normal-event PID, validates observer breakpoint restoration and
detach-without-kill, checks that the process survives, pauses that same PID,
verifies explicit same-PID bridge attach, passes the exact driver object into
the lifecycle continuation, and invokes one outer cleanup on both success and
failure. The C++ observer supports this handoff, but the old standalone Python
capture runner remains invalid as an inner phase because its `finally` kills
the CK3 process it launched.

The package deliberately has no concrete normal-launch/UI/observer/bridge
adapter yet. Until that adapter implements the injected operations, the next
CK3 command remains **NO-GO before launch**. See
[the lifecycle runner record](g2-source-specific-war-loss-lifecycle-runner-2026-09-05.md)
and [the outer-owner record](g2-source-specific-war-loss-outer-owner-2026-09-05.md).

## Source-capture success fields

The first phase may continue only when raw `capture.json` has every field
below:

- `schema="raiktor-war-bound-private-capture-v1"`;
- `status="private_test_only"`, `result="GREEN"`, and
  `reason="six-action-bound-source-executions-captured"`;
- `read_only=true`, `public_bridge_abi_changed=false`,
  `production_detour_installed=false`, and `readiness_promotion=false`;
- exact EXE SHA `2D00...DB86`;
- `observation_stop_rva="0x2E7F951"` and
  `observation_window_end_rva_exclusive="0x2E7F9A6"`;
- arm SHA `B7DC28B0B9EDB0F8A03E5DB2F03AD6CA1E3B649648BAE161B6A487063735B9B8`,
  event `bookmark.1071`, option `bookmark.1071.a`, index `0`;
- `source_execution_count=6`, six rows ordered by `sequence=1..6`;
- six distinct nonzero `loaded_node` values and six distinct full-generation
  `army_generation_id` values;
- one nonnegative full-generation `exact_raiktor_war_id`, equal to every
  execution `war_id` and every persistent-regiment `war_id`;
- each execution has nonempty `current_regiments` and
  `persistent_regiments`; current generation IDs are globally unique,
  persistent generation IDs are globally unique, and the persistent-to-current
  mapping is complete and one-to-one within each execution;
- each execution `initial_soldiers` equals the sum of its captured
  `current_soldiers`; no authored `500` or `3000` assertion is permitted;
- `breakpoint_installed=true`,
  `original_breakpoint_byte_restored=true`, `attach_mode=true`,
  `debugger_detached=true`, and `process_terminated=false`.

Immediately normalize that raw capture, before any readiness decision, with
an absent output path:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B `
  "ck3_autonomous_player\native_bridge\research\prepare_raiktor_source_specific_war_loss_capture.py" `
  --contract "ck3_autonomous_player\native_bridge\research\fixtures\raiktor_source_specific_war_loss_attribution_v1_contract.json" `
  --capture "<fresh-attempt>\capture.json" `
  --output "<fresh-attempt>\source-normalization.json"
```

The normalized output must contain a nonempty `source_set_sha256`, the same
WarID, exactly six executions, and complete `army_generation_ids`,
`persistent_generation_ids`, `current_generation_ids`, plus the measured
initial soldier total. This phase still leaves
`private_live_evidence_classified=false` and
`source_specific_loss_ready=false` until review and lifecycle completion.

## Same-lifecycle stage gates and stop conditions

Every later record must repeat the raw capture PID, the exact WarID and the
normalized `source_set_sha256`. After bridge attach it must additionally keep
one `connection_generation` and one `episode_run_id` through termination,
cleanup and expiry.

### 1. Current checkpoint

Continue only after two read-only queries on one paused frame return the same
normalized payload and bind every queried Army/current/persistent generation
to the source set. Record per-generation current soldiers and their measured
sum. This is the last pre-termination current checkpoint; it is not assumed to
equal the creation-time total.

Stop RED, preserve the attempt and perform managed cleanup if any source
generation is missing, duplicated, bound to another WarID, already stale, or
if PID/generation/episode/frame identity changes. Do not issue surrender after
a RED current checkpoint.

### 2. Typed termination

Exactly one mutation is allowed:
`surrender-war-<exact full-generation WarID>`. Its result must be exactly one
native-headless ACK with matching step, `accepted=true`, and
`status="submitted"` (or the adapter's already accepted terminal status).
The game date must not be advanced by a separate command.

Stop RED before a second action if the ACK is malformed, rejected, duplicated,
or bound to another revision/WarID. Never retry the surrender inside the same
attempt.

### 3. Postwar cleanup and persisted expiry

First require two stable paused postwar snapshots in the same PID,
connection-generation and episode. Old WarID absence is only admission to the
cleanup query; it does not prove destruction.

The private cleanup query must return `status="destroyed"` for the exact frozen
generation vector, with no stale army attachment, `post_termination_soldiers=0`,
and proven boundary loss equal to the measured current checkpoint total. Then
query `query-raiktor-actual-truce-expiry-v1-<retained primary defender full
generation ID>` twice. Both rows must bind the same PID/generation/episode,
have successor query sequence numbers, and return equal available expiry
payloads. Only then may the retention ticket be consumed and one
`persisted_native_truce_row` be written.

Stop RED and preserve the attempt if cleanup reports alive/unavailable, the
generation vector differs, WarID absence is the only evidence, expiry is
unavailable/unequal, or any lifecycle identity changes. In all GREEN and RED
cases, finish by proving bridge/observer detachment, driver closure, CK3 and
injector process count zero, and immutable source hashes unchanged.

## Readiness boundary after a successful run

A qualifying artifact may establish a private source-specific loss input for
the existing comparison consumer. It does not by itself provide campaign
dominance, owner-budget or white-peace providers. Public/action/decision/
automatic-surrender readiness and `GEN-034` remain false until their separate
gates are satisfied.
