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

## Next bounded work

Repair the generator sources for the three workforce fact files using the
documented CK3 calculated-value rule (materialize the arithmetic in an effect
variable, then compare the scalar in triggers), add generator/static
regressions, and run offline checks only. A new CK3 launch requires a separate
explicit gate decision; this attempt is not to be rerun.
