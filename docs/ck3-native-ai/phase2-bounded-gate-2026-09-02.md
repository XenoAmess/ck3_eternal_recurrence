# ZhongGuo phase-two bounded gate (2026-09-02)

This is the one new exact-build bounded seed attempt requested for the phase-two
priority blocker. It is evidence, not a release claim.

## Frozen inputs

- Source: `8c7e9ceb5a5aadcbf82ac9632422e5972f83a412` (`origin/master` at gate
  start), including the China tutorial-prompt settings fix.
- CK3: `1.19.0.6`, executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Game tree: the project copy at `Z:\ck3_mod_rewrite\Crusader Kings III`
  (the Steam tree and overlay were not used).
- Bridge: `xar_ck3_bridge.dll` SHA-256
  `B018FB8C55E99E915E728166BBF1934518095CF4E4981114970FC0CEE69026F0` and
  injector SHA-256
  `8F4E9C6E36BA50B976909E3AC54B3B6A655F39EBED81F42993E517F0E40BF65D`.
- A fresh profile and named pipe were used. No prior checkpoint or Steam
  overlay was mounted.

## open_kaishek offline preflight

Artifact: `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\open-kaishek-preflight.json`.
The CLI was built from `open_kaishek` commit `b306a95`; the shaded jar SHA-256
is `1EA26AB19761CAB14EECA2E2D106B7353D9CBD606BA091D3C0EF8C67D2AA4A8B`.
The command used profile `ck3-1.19.0.6-zg361` and fixture
`synthetic-361-014`.

The preflight is intentionally layered: parser `GREEN` (root and combined),
synthetic IR `GREEN`, and synthetic runtime `GREEN` (`execution=SUCCESS`).
The root/combined validator is `RED` with 92 `UNKNOWN_OPCODE`/
`WRONG_DOMAIN` diagnostics because this profile is explicitly
`schema-only`; it does not certify full CK3 semantics. Overall CLI exit is 1,
so this must not be reported as an overall offline `GREEN`.

## Gate attempts and result

Two launch-boundary setup failures are retained separately:

1. System `py` stopped before CK3 because `pyautogui` was unavailable.
2. Project virtualenv had `pyautogui 0.9.54`, but the first retry used a pipe
   name outside the runner's required 32-lowercase-hex contract.

Neither setup failure launched CK3. The final contract-valid attempt used one
fresh profile and one fresh pipe. Its report is:

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\artifacts-final-8c7e9ceb\runner-report.json`

Report SHA-256:
`75B939210DF1D502AA4B635159F776D9A143D9675A6954F73A787A5AF5EBF5B5`.

Result: `RED` at loader `database_init` (`event_wait_authorized=false`). CK3
did bind the native MCP pipe and the exact-build adapter reported a matching
build, but it never reached Load Save/In Game or a paused frame. No provider
query, seed capture, or capability claim was made. CK3 exited with code 1;
managed cleanup and driver close were `GREEN` and no CK3 process remained.

The loader recorded 15 fatal script diagnostics, all in the workforce fact
effects:

- `zg361_workforce_rehire_fact_effects.txt`
- `zg361_workforce_exit_fact_effects.txt`
- `zg361_workforce_normal_exit_fact_effects.txt`

The diagnostics are `Unknown trigger: value`, `add`, and `subtract` caused by
calculated-value blocks on trigger-side exact equality. This is a startup /
readiness RED, distinct from the previously known particle2 null-slot crash;
that crash was not repeated.

The runner also recorded six generated Python bytecode files during its static
preflight, making its source immutability after-check `RED`. Those files were
removed after the run; the retained report is not rewritten and therefore
continues to document that boundary accurately.

## Offline repair follow-up (not live evidence)

The three generator sources were repaired without hand-editing generated files.
Every trigger-side computed equality now uses the documented inclusive pair
(`>=` and `<=`) with the same calculated-value RHS; effect-side
`set_variable`/`change_variable` arithmetic was left unchanged.  Regenerated
outputs contain zero direct computed-variable equality guards in the affected
effects (the forbidden shape is `var:<name> = { value = ... add/subtract/multiply }`),
including the previously unreported #277 consume guard.

Focused generator contracts are green: rehire 25 tests, exit 26 tests, and
normal-exit 29 tests.  `tools/validate_static.py` is also green.  The bounded
offline parser pass using the same open_kaishek CLI produced `PARSED`, zero
diagnostics, and `roundTrip=true` for each repaired effects file; artifacts are
under
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postfix-parser\`.
The formal preflight's 92 validator diagnostics remain the declared
`schema-only`/`UNSUPPORTED` boundary and are not reclassified by this parser
pass.  No CK3 launch was repeated; a future loader gate must be separately
authorized.

## 2026-09-02 03:12 offline preflight refresh

After the narrow `open_kaishek` profile slice (`d207707`), the same product
root was preflighted with the rebuilt JAR
`CBCD5F868F5C46AA7B5A2C70E11705B978F95DE3437E0809D20A4139F62DD0E4`.
The machine-readable artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-d207707.json`
with SHA-256
`570BB393FC84E3E87AE69141AF1D036FC63434BB410B9F99A17F197F032DC2D8`.
It completed in `3.144s`: parser `GREEN` (76 files, 0 diagnostics), fixture
IR/runtime `GREEN`, and bounded root validator `RED` (233,708 diagnostics).
This is an offline schema boundary, not a CK3 loader result; no CK3 process,
save, or network was used.

## 2026-09-02 03:16 delta isolation gate

The only follow-up CK3 attempt used a source candidate that was byte-identical
to the current parent tree except for removal of the 249-line d692 role-failure
block in `zg361_workforce_exit_fact_effects.txt`.  The candidate passed source
archive equivalence, static preflight, bridge identity, and exact-build
dependency checks.  Its source tree SHA was
`1b1db97883b4eb65b8a221aa888476587c19c5d71f808a3c82bb58da5fc37583` and the
source ZIP SHA was
`145b466757fec58ff7fbe3ab5c74cd807f9d9454447eadf90fbad7f948f27499`.

The retained report is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\delta-live-pre-d692-20260902\artifacts\runner-report.json`
with SHA-256
`9EA7AFBEBCD210997B77F794574E7D36FEE3CA1C700C02EE707FE7389F9DF460`.
It is `RED/LoaderStageTimeout` at `database_init` after `299.9s` (quiet
`141.194s`), with `fatal_error_count=0` and no Frontend, Load Save, or native
readiness.  The candidate also exposed one concrete dangling reference:
`Unknown effect: zg361_workforce_exit_fact_verify_role_failure_publish_effect`
at `events/zg361_workforce_exit_fact_events.txt:64`, because the removed block
owned that effect.  Therefore the removal is not a shippable fix and was not
merged.  Cleanup/driver close and external dependency immutability remained
GREEN; no further same-shape CK3 attempt is scheduled until a new compatible
stub or call-site change is statically prepared.

## 2026-09-02 03:24 compatibility-candidate closure

The proposed compatibility follow-up was checked offline against the retained
delta tree and was intentionally not merged. Removing the d692 role-failure
block leaves the event call at
`events/zg361_workforce_exit_fact_events.txt:64` pointing at the undefined
`zg361_workforce_exit_fact_verify_role_failure_publish_effect`. A no-op stub
would hide that parser symptom but would fail generated-output parity and the
role-failure contract tests (4 exit tests fail); removing the call leaves the
same parity/semantic failures. The intact generator output parses cleanly
with open_kaishek and `tools/validate_static.py` is GREEN, so this candidate
does not explain or repair the independent `database_init` timeout. No
production source or branch was changed. The next phase2 code change must be
an evidence-backed loader/readiness fix, not a compatibility stub for this
invalid delta.

## 2026-09-02 03:28 evidence-backed schema increment

`open_kaishek` mainline `1c320ad` adds only the two scalar triggers already
marked `[static-confirmed]` in the exact-build ledger:
`has_game_rule` and `has_character_modifier`. Its rebuilt JAR is
`F01C9D5FD0095960AC58E20031F22A3A28F0AFA5B0716C4D3DBECE49583C8A1A`.
The retained offline artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\postschema-preflight-1c320ad.json`
with SHA-256
`A63212B2F5BFAE1FEFE280DEAC1D75D77720A13BD5A46430876094D86D294F22`.
Parser and fixture IR/runtime remain GREEN; the bounded validator is RED at
`233,115` diagnostics, 601 fewer UNKNOWN diagnostics than `d207707`. The
eight additional WRONG_DOMAIN diagnostics are existing SCRIPTED_VALUES
coverage boundaries, not a schema expansion. Focused profile/validator Maven
tests and the CLI preflight passed; CK3 was not started.
