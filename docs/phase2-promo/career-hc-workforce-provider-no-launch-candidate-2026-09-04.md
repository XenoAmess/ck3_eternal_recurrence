# Career-HC/workforce provider no-launch candidate (2026-09-04)

Status: **static-ready / live-pending**. This audit starts from canonical
`ce458af71a2a44decc085766720082a8b724edb8`. The source candidate is
`6a6473ac5b4e9afcb406915cd1f61b5cf619a40a`. No CK3 process was started,
no gameplay action was submitted, and no live provider result is claimed.

## Integrated source contract

The read-only query remains
`game.command.query-zhongguo-career-hc-workforce-postcondition-v1`. It reads
only the fixed six career-HC buckets, the conservation flag, manager cost, and
the exact M360 receipt identity. Caller-selected variables and arbitrary
character reads remain forbidden. Application-main mailbox slot 26
(`permitted_executor_sexvigintary`) has 14 fixed allowlist reads.

The adapter now derives its descriptor size from a 76-capability base. The
projects/metrics candidate alone produces 77 capabilities, the career-HC
candidate alone produces 77, and both private candidates produce 78. This
removes the eight stale literal-count source-contract failures found after the
B4/provider integration. The build helper also accepts an explicit read-only
`-Ck3ExecutablePath`, so an isolated worktree can run all exact-build tests
against the canonical 1.19.0.6 executable without copying the ignored game
tree into the worktree.

`XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1` defaults to
`OFF`. Turning it on adds only the already-wired query capability to a private
candidate descriptor. Default production advertisement remains absent. A
transport ACK cannot satisfy the query contract or make the cell GREEN.

## Correct VS x64 regression

Both builds used Visual Studio 18 Community's `vcvars64.bat`, MSVC
`19.51.36248.0`, Visual Studio's CMake/Ninja, Release configuration, and the
exact CK3 executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
No CK3 process was invoked.

- Default-OFF build `Z:\b6hci2`: 480/480 build steps and 92/92 native tests
  GREEN. Its bridge SHA-256 is
  `05857D9BDB2212A286445B884B2D66FCEF7792013F9283791896B3D7C3A96C0C`.
- Private candidate build `Z:\b6hcic`: 480/480 build steps and 92/92 native
  tests GREEN.
- Candidate-focused adapter/provider/mailbox selection: 3/3 GREEN.
- Focused Python contract, action-cell, route checkpoint, and verifier suite:
  34 passed plus 7 subtests.
- B6 no-launch preflight and the B4 route-B checkpoint preflight: GREEN.

The exact native-source fingerprint for both builds is
`C640BEDF73A1789D1E28CBD41F60A86E12E08F643345E99B5D666DCC599DA39C`.

## Frozen private candidate

The immutable candidate pair is stored at
`Z:\ck3_mod_rewrite_process_assets\zg361\career-hc-workforce-provider-private-candidate-6a6473a-20260904T062648Z`:

- `xar_ck3_bridge.dll`: 2,352,640 bytes, SHA-256
  `9EE39CAE349180806FA2631805539EFC704C45401A2EB11F7F781F4EE671E7AC`;
- `xar_ck3_bridge_injector.exe`: 39,936 bytes, SHA-256
  `751D178F692EA029F84A0D4DDA00BDA09C2DB2F85AFAD49833BE0DF8D3C9A994`;
- `CMakeCache.txt`: SHA-256
  `EE8D067DD6CC5453A2DD0F971EA72E223BB4490C019FEF9F75462D3F674EB2BC`,
  with career-HC `ON`, projects/metrics `OFF`, and the exact executable path.

The machine-readable manifest also pins the base/candidate commits, all
provider, mailbox, bridge, schema, service/MCP, B6 cell, and B4 route-interface
source hashes, the native source fingerprint, the binary pair, cache, and CK3
executable.

## Reproducible default-off preflight

From this worktree root:

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools/verify_zg361_career_hc_workforce_no_launch_candidate.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_career_hc_workforce_postcondition_v1_no_launch_candidate_20260904.json --check
```

The verifier is read-only. It proves that the source option still defaults to
OFF, the candidate capability remains preprocessor-guarded, the default
projection withholds it, the frozen cache opted in against the exact executable,
and every pinned file and binary hash matches. It also rechecks B4's exact
`zg361we.360` route B interface: native option index 1, submitted option 2,
13 Workforce facts, same-paused-revision join, and ACK-not-result semantics.
It does not create an attempt directory, inspect or start processes, inject a
DLL, or modify the formal runner.

## Live checkpoint still required

The reserved attempt
`zg361-career-hc-workforce-6a6473a-20260904T062648Z` remains absent. A later
serial CK3 live owner must start from the current cumulative projection,
activate the Workforce transition fixture, and pause on the real
`zg361we.360` before selecting route B. It must freeze exact owner, distinct
subject, date, event instance, save bytes and product/fixture hashes; submit B
once; retain the option response as ACK only; then query both providers on the
same paused revision after rebinding to the subject without date advance.

GREEN requires B4's 13 Workforce facts plus this provider's exact state-4,
choice-2 M360 receipt, six available/reserved/occupied/frozen/reclaimed/
authorized buckets, a true conservation result, and manager cost zero. Until
that retained live frame exists, readiness and production advertisement remain
unchanged: `static-ready-live-pending` and default OFF.
