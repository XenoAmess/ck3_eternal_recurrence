# G2 postwar cleanup / expiry current-pin no-launch freeze

## Result

[static-ready / formal no-launch / serial live pending] The corrected R2 candidate
is bound to runtime source `4da52808301ba16e92f5097c69ab541f4938d587`,
the exact CK3 `1.19.0.6` executable, one native DLL, one 86-file production
projection, and one unique cold-checkpoint command. The formal preflight
returned `READY_TO_SERIAL_LIVE`; it did not prepare a profile, start CK3, or
attach the injector. Before/after inventories both contained zero `ck3.exe`
and zero `xar_ck3_bridge_injector.exe` processes.

The frozen manifest is
`ck3_autonomous_player/native_bridge/research/fixtures/g2_postwar_cleanup_expiry_current_pin_live_manifest.json`.
The verifier is
`ck3_autonomous_player/native_bridge/research/prepare_g2_postwar_cleanup_expiry_current_pin_capture.py`.
The future live runner is
`ck3_autonomous_player/native_bridge/research/run_g2_postwar_cleanup_expiry_live_acceptance.py`.

Formal artifact root:

`Z:\ck3_mod_rewrite_process_assets\zg361\g2-cleanup-formal-4da5280-r2-20260904`

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `no-launch-preflight.json` | 16,472 | `11D4109E387E0D4FCC4C371FFF097EB05308112C0769EB0D7B016E5E5DC2CF0C` |
| `frozen-candidate-manifest.json` | 12,574 | `83D04FD8E3E24918ACB1C5B617401397763E87C997F7BD75E45389BE7896D19E` |
| `live-r1-case-mismatch-report.json` | 5,461 | `F120638D4B50050A9B43687E6DA5C16C4DA32DCDA542BBFB6AFEB6358B55DF5F` |
| `xar_ck3_bridge.dll` | 2,466,304 | `4D839524098891BD997009663E189929722746AB0404D88C1E91F7546EFE238B` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `43983E28CE3FBFC5EA1F26786834AD5E9133E59807BDCB18FB244BA8E830E08D` |
| `CMakeCache.txt` | 19,223 | `2647ADE26116BB5E27017361B7F3981F3CF0FFA12D53B7D73E820C8DD14C4A3F` |
| `native-ctest.txt` | 37,508 | `EF7001A319FC4661C6A3113283CB505F729E088CAD87884140203CE421CB192E` |
| source ZIP | 83,905,147 | `C124711B719DD4D9967584CC9C9EE33EFD7C50460DFF48CA4D8B726479EBA273` |
| product manifest | 15,864 | `284E162CEFB7A15A77CC11FD7DB4D7B429C4F40A8EEF2FCA453BC2C6B614BFF5` |
| product ZIP | 2,728,187 | `DC43D4376C42DB4FB5DBA41EA36BD4BE5529A3F77CE98D337A5C2A1DE4133E3A` |

The product row above is informational; the committed manifest is the
machine-readable authority. The production tree contains 86 files and has
tree SHA-256
`F4E63FFFA6CF9332BA41EB5985D1CB72F280F4BF375A15473F4638F43CF944BE`.

The first final-pin no-launch call found another work package's CK3 PID `60080`
and correctly returned a harness/slot RED before any profile preparation or
attachment. That attempt is retained as
`no-launch-preflight-red-occupied-pid60080.json` (14,163 bytes, SHA-256
`BF015166790F4F278E305EA9C6F695CFA52709E529B9552AC5C2DE7BA369BA5C`).
After that process exited, the unchanged verifier and manifest returned an
initial GREEN. The source pin list was then expanded to cover every cleanup,
expiry and G2 runtime dependency, and the final manifest was run again to
produce the formal GREEN above. The occupied-slot result was not a G2
capability failure, and this package did not terminate or interfere with the
other process.

The first authorized R1 command then returned a reproducible pre-session RED
after 3.353 seconds. Its preparation result contained lowercase
`f4e63...944be`, while the frozen CLI value contained the identical digest in
uppercase. The base runner compared those strings directly and raised
`prepared production tree differs from the frozen short-path product` before
creating the session thread. The retained report has `session=null`; CK3 and
the injector both remained at zero. This is a harness RED, not capability RED.

R2 applies the minimum evidence-backed correction: both operands are validated
and normalized as 64 hexadecimal digits before equality comparison. The
focused regression proves lowercase/uppercase equality and still rejects a
different digest. The fresh `live-r2` directory remains absent, so the command
below can be executed once without reusing R1 state. The focused runner,
preflight, receipt, cleanup, expiry-contract and `open_kaishek 37cab82`
compatibility set is `28/28 GREEN`.

## Why the candidate was rebuilt

The earlier `971d1f9` candidate passed all tests, but canonical advanced to
`b8ecfdf` and changed `native_bridge/CMakeLists.txt` plus
`src/ck3_11906_adapter.cpp` for the B3 compensation capability. Those files
are part of the native build, so the old DLL/source ZIP could no longer be
called the current canonical candidate. The DLL was therefore rebuilt and
tested. Canonical then advanced to `549076f`; native and mod-product bytes did
not change, but the G2 Python runtime pin in
`raiktor_surrender_truce_contract.py` did. The final source/product package was
advanced again through the current `open_kaishek` pin `37cab82` and the
observed R1 runner correction at `4da5280`. The already tested DLL remains
byte-exact because its complete native source set is unchanged, and the
production tree remains the same 86-file hash.

This is not a new runtime dependency on B7. B7 is present in canonical through
integration commit `6bfbad2a8f7e549f917f9c29ff1f9514bc85004c` (underlying source
candidate `7d50c2d3b739221e216c5158a04b6d18bf6b3587`), but the G2 receipt
does not query or consume a B7 promotion observation. Therefore
`required_as_g2_runtime_input=false` and `new_freeze_required=false`. Runtime
drift after `549076f` led to this replacement freeze. Any native, product or G2
runtime dependency change after `4da5280` invalidates R2; native drift also
requires a new DLL.

## Exact build and product binding

MSVC `19.51.36248.0` built x64 Release with only these private candidate
options explicitly enabled:

- `XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1=ON`;
- `XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=ON`.

All adjacent G2 capture/observer options and all Phase2 observer candidates
listed in the manifest were OFF. Their source defaults also remain OFF. Full
native CTest was `94/94 GREEN`, including both providers, the private dispatch,
the adapter registry, and the current B3-native source. The exact CK3 EXE
SHA-256 remains
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

The release manifest is format 2, records Git source `4da5280`, and verifies
every one of its 86 staged files. The live runner additionally checks the
prepared short-path production tree against the frozen tree hash before its
session thread can start. Thus a later mod/product drift becomes pre-launch
RED rather than a run against different content.

## Fresh short path and evidence rule

The unique R2 command is stored as an argv vector in the committed manifest and
rendered into the preflight report. It directly restores the exact in-war
checkpoint and driver state; there is no lobby replay and no OCR. It is still
default-OFF and requires the explicit `--authorize-private-live` argument.
When the exclusive CK3 slot executes it, the one intended sequence is:

1. produce two equal paused public terms queries and retain the exact
   full-generation war-bound vector for WarID `50331699`;
2. submit exactly one private native `surrender-war-50331699` command;
3. admit the postwar tail only after the old full-generation WarID is absent
   on a stable paused successor frame in the same PID, connection generation
   and episode;
4. dispatch the private exact-store cleanup reader once, then query the
   persisted actual expiry twice on that same paused frame;
5. pass only if the cleanup reader itself reports every frozen generation
   destroyed and both persisted future expiry reads are equal.

WarID disappearance is only admission to step 4. It is never converted into
`destroyed`, zero soldiers, or a loss amount. A `still_alive`, unavailable,
mixed-generation, unstable, or mismatched result is capability RED and must be
retained as such.

## Remaining G2 iteration

This package adds no production-live evidence. The next G2 step is the single
serial action-bound live command from the manifest. A GREEN receipt would
unlock comparison-layer consumption of observed cleanup and actual expiry, but
would still leave public action readiness, automatic surrender, and `GEN-034`
open. `GEN-034` also needs the wider continue/white-peace/surrender comparison,
budget/campaign inputs, and remaining source-specific attribution before an
automatic choice can be claimed.

Current boundaries are therefore all false:
`source_specific_attribution_ready`, `public_readiness_promoted`,
`action_readiness_promoted`, `decision_ready`, `automatic_surrender_ready`,
and `gen034_closed`.

No CK3 effect file was changed by this native/Python work package, so the
effect-file 1–10 target and 20-effect ceiling were not exercised. No load-time
or file-boundary performance RED occurred in these no-launch checks.
