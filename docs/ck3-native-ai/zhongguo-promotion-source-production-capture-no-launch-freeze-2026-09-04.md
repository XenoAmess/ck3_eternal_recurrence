# Promotion source production capture: frozen no-launch candidate (2026-09-04)

## Status and boundary

This package freezes one `static-ready-live-pending` candidate for a future,
serial production capture of the real `zg361pp.147` promotion source. It does
not start CK3, write a checkpoint, advertise either new production capability,
or treat an action ACK as a business result. It changes no production source,
formal runner, generated effect, or effect body.

The implementation baseline is integrated B7 commit
`d53befaa4872662562f5db5d31757ca731e799e0`, observed from canonical
`366f30f0e899650582a7f76c8f0043ecc37e4887`. The frozen native target is CK3
`1.19.0.6`, executable size `95,206,008` bytes and SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

## Frozen external candidate

The repository manifest is
`ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_promotion_source_capture_no_launch_candidate_366f30f_20260904.json`.
Its external, append-only copy and native binaries are under:

`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-366f30f-20260904T082656Z`

| File | Bytes | SHA-256 |
|---|---:|---|
| `xar_ck3_bridge.dll` | 2,418,688 | `40AE9BC83C7640D09CD35BDD3FBE10C079E7AFFFA55E626AE0E47710F8D72667` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `5809144E895DE6FE6BEBF29C2310BBC2313E3B8E2262CEBB175478EFDA79E9E3` |
| `CMakeCache.txt` | 19,723 | `B92173960B12E9370B401C5FC842D4C795B0CE8DF77224EE4A330CDC770BD511` |
| `frozen-candidate-manifest.json` | 12,329 | `4268B6D147D234536A03A98EC1F7A5E08DAAA7246DFF340B51FD42E2E94A8F98` |
| `no-launch-preflight.json` | 6,992 | `1A4900AABE5D3FD0BA582F8AE9199919A27F27EDCCD9319F1A1D52B9B483EE88` |
| `no-launch-preflight-red-existing-ck3-pid13740.json` | 7,000 | `66C5FD65A617EAD248FAE2578DFE9AD1F2F4CE0C8C382E92EF85769BF86DBBBB` |

This was a fresh MSVC/Ninja `Release` default build. Its cache records both
unrelated private candidate toggles as `OFF`. The build completed 489 compile
and link steps, then passed all 93 native CTest cases. The first fresh discovery
run exposed six older source-contract tests still frozen at the pre-B7 adapter
count 76; only those test literals were updated to 78, after which a second
empty build directory reproduced 93/93 GREEN. That failure and repair remain in
the manifest rather than being hidden.

The first machine preflight also correctly returned RED while another serial
work package owned CK3 PID 13740. That failed report is retained above. After
that process exited normally, the same immutable candidate returned
`READY_TO_SERIAL_LIVE` with zero CK3 and injector processes; the future live
attempt directory remained absent. This package did not start or terminate the
other process.

## Capability and player gates

The no-launch verifier reads the native header, adapter registry, ABI and source
contract rather than trusting descriptive manifest fields alone. It confirms:

- `game.command.query-zhongguo-promotion-source-progress-v1` and
  `game.command.activate-zhongguo-review-now-v1` are both unadvertised;
- only their named fail-closed transport capabilities are present, so readiness
  remains `live-pending`;
- the product action is rooted at `GetPlayer.MakeScope`, never a caller-selected
  character;
- the scripted gate requires `is_ai = no`, a celestial liege, the real review
  business-valid trigger and at least 150 prestige; execution deducts exactly
  150 prestige and sets the one-shot `zg361_review_now_pending` flag; and
- neither a transport ACK nor an event-option ACK is accepted as the review,
  promotion, compensation or checkpoint postcondition.

## Required production choreography

The frozen entry accepts only the managed product path. It observes the played
owner and the same connection generation, invokes the exact review-now action
when needed, waits for a real paused `zg361pp.146`, selects option index `1`,
advances through the managed product service, and accepts only an independently
observed paused `zg361pp.147` at least one in-game day later. The path is bounded
to 400 in-game days. The capture then saves the real game state and emits the
schema-2 single Promotion entry; it remains explicitly incomplete for the
canonical four-entry registry.

Fixtures, console commands, generic character rebinding, direct CK3 invocation
and direct injector invocation are excluded. The future live attempt directory
is uniquely reserved as
`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-live-attempt-366f30f-20260904T082656Z`
and must still be absent when the preflight is run.

## Effect boundary evidence

No effect file was changed by this freeze. The verifier independently parses
the generated trees and pins their aggregate fingerprints:

| Purpose family | Files | Effects | Per-file range | Fingerprint SHA-256 |
|---|---:|---:|---:|---|
| feedback / promotion / PIP | 39 | 275 | 1–10 | `94042BE37F3950D21F8B6AB39F9E1206B431A90CB9ACB51A6D9E814693B8CB4A` |
| compensation / LTI | 25 | 148 | 3–9 | `9F7041818149A0F532CE1A6C217C77240F2C17019D63B3D0FD087619CBC29B5C` |

Both families meet the requested 1–10 target, neither needs a greater-than-20
exception, both generators pass `--check`, and the two superseded monolith
filenames are absent. This preserves the file-boundary/load-risk lesson as a
live precondition instead of relying only on generated parity.

## Single authorized CK3 command

After the no-launch verifier is GREEN and the CK3 serial gate is acquired, the
following is the only authorized launch command for this frozen attempt. It has
not been executed by this package:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_zhongguo_acceptance.py" "--artifacts-dir" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-live-attempt-366f30f-20260904T082656Z" "--phase2-promotion-source-checkpoint-live" "--phase2-promotion-source-checkpoint-timeout-seconds" "600" "--bridge-dll" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-366f30f-20260904T082656Z\xar_ck3_bridge.dll" "--bridge-injector" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-366f30f-20260904T082656Z\xar_ck3_bridge_injector.exe" "--bridge-pipe" "\\.\pipe\xar_ck3_bridge_zg361_9de2ca28a89041abbe216fd9a56026ed" "--phase2-seed-contract" "Z:\ck3_mod_rewrite\tools\zg361_phase2_seed_contract.json"
```

The manifest stores the same command as a 15-element `argv` vector; the
verifier rejects extra, missing or reordered arguments and requires the formal
runner to own the CK3 lifecycle.

## Static evidence

- fresh native build and CTest: `93/93` GREEN;
- promotion-source contract unit tests: `4/4` GREEN;
- source checkpoint capture tests: `5/5` GREEN;
- source checkpoint runner tests: `4/4` GREEN;
- frozen candidate verifier tests: `5/5` GREEN, including rejection of enabled
  production advertisement, ACK-as-result, command drift, effect drift and a
  false live claim;
- source capture no-launch preflight: GREEN and
  `incomplete_for_canonical_4_entry_registry = true`;
- feedback/promotion/PIP and compensation generators: both `--check` GREEN;
- `tools/validate_static.py`: GREEN.

The machine preflight must additionally prove that neither `ck3.exe` nor the
injector is running before it emits `READY_TO_SERIAL_LIVE`. Until the one real
attempt produces its paused snapshot, save and schema-2 artifact, the honest
status stays `static-ready-live-pending`; the result provider remains default
off.
