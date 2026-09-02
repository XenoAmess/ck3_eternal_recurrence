# Phase 2 canonical-seed live attempt at `82d6b77` (2026-09-03)

## Result and evidence boundary

The one authorized canonical-seed attempt ended typed **RED** before native
readiness. It did not generate a candidate seed, capture, or loaded-seed proof,
and it must not be repeated with the same source and observation surface.

The runner reported
`loader_terminal_missing_after_database_completion_publish`: the exact
completion publish at `0x3B9CFD7` was observed, but the process remained in
`database_init`, `event_wait_authorized=false`, `native_readiness=null`, and no
candidate was materialized. The error log was empty and the loader reported
zero fatal errors. This result therefore leaves the canonical Phase 2 seed and
all downstream footage at pending; it is not `paused_seed_ready`.

## Frozen candidate

- exact source: `82d6b774edb7a6edbaca04c0aa4a27d7d88661a7`;
- required ancestry: seed readiness integration `0bf047f` and histogram gate
  `a315d55` are both ancestors;
- clean source:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\source`;
- source ZIP:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\head-source.zip`,
  SHA-256
  `0C5D3C41F105F6525D4BDDD0C4B1CE091AE81AF2C2914889DD55A42FDFDCEF7F`;
- clean-source tree SHA-256:
  `94826C5779F0AB239B150C1533BDC8860C95B895A921D240E2C4D763E17C75C7`;
- CK3 executable SHA-256:
  `2D00FF3101EF70B566F2FCBA292F09263199C80E9DC8F139B82D7D96F83DB86`;
- fresh bridge DLL SHA-256:
  `205B9A1647A34E52CF3140679ABEEC48E4E7CFD5744E044EC353D406B9D60610`;
- fresh injector SHA-256:
  `ABCF1AFBC75F7743D4FD9CFBA67772128FA0699E1E3AF7B515BE0EB99A5EFB53`.

The short-path MSVC/Ninja build completed all 384 compile/link steps. The
Phase 2 observer plus suspended/running injection focused slice passed `7/7`.
The full CTest run retained the integration baseline of `62/77`, with the same
15 already documented source-contract/harness failures; none was a compile or
link failure, and this attempt does not relabel that full suite GREEN.

## No-launch preflight

The accepted preflight ran from `2026-09-02T17:25:56.118259Z` to
`2026-09-02T17:26:10.035535Z` and returned
`GREEN / preflight-ready`. Static preflight, source/archive equivalence,
product+fixture projection, process inventory, dependency immutability,
clean-source immutability, and runtime-projection immutability were all GREEN.
It did not start CK3.

- artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\preflight-attempt3\artifacts\preflight.json`;
- artifact SHA-256:
  `BC30A41E118556D4CF022CF3F31360286B5A5B65ED28672FB1EC6FF27CC10B33`.

Two earlier preflight-only command attempts are retained as typed, no-launch
CLI failures: one had an extra escaping layer in the pipe value and one had a
missing leading slash. Neither crossed the CK3 launch boundary or created a
game PID.

## Unique live attempt

- runner interval: `2026-09-02T17:26:43.759424Z` through
  `2026-09-02T17:32:09.958266Z`;
- CK3 PID: `9904`, one generation, no restart;
- pipe:
  `\\.\pipe\xar_ck3_bridge_zg361_8e5c820a35c64ff9b6932eb6d6bc3ca4`;
- terminal stage: `database_init` after `299.805` seconds;
- observed database nodes: `CGameConceptTypeDatabase` and
  `CJominiLoadScreenDatabase`;
- completion publish: observed at `0x3B9CFD7`;
- post-init rows: `0`; event wait: not authorized; fatal errors: `0`;
- candidate, capture, provider probes, and native readiness: absent.

The shared action-aware legal/notice handler returned `GREEN / no_modal` and
made zero clicks. No coordinates or gameplay visual control were used. No
Steam, Paradox Store, external purchase, payment, order, checkout, or other
real-money action occurred.

## Artifacts and cleanup

- runner report:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\live-attempt\artifacts\runner-report.json`,
  SHA-256
  `3A7D162EA755D72A531614C85AE54B629833217CC81C31AD05CA46543BF1B7E7`;
- loader progress:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\live-attempt\artifacts\01_phase2_loader_stage_progress.jsonl`,
  SHA-256
  `3843E3586EC6C33916FA9B07200602FEB45D4BFED3D83D76D1CDE6F20F63B596`;
- legal artifact SHA-256:
  `9895520AEA509A821E81D1B6E2A28F95EF08AEE859B3337EDDE73D9D0B497395`;
- cleanup artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-live-20260903T011900-head-82d6b77\live-attempt\artifacts\09_phase2_native_session_cleanup.json`,
  SHA-256
  `4AD8B2778F63A953D3FD0BA970AB13CE8D7F388CE0D8E7284F8C2C023D8CD08A`;
- frozen debug log SHA-256:
  `5CFED2847DF315B44C1EAF39BC6DDA9F4C292977974D4B4DC6CB83440D39150A`.

Cleanup is GREEN. PID `9904` and its process tree are gone, the Job is empty,
the watchdog and control files are absent, the driver is closed, and the final
global CK3/injector inventory is empty. Source ZIP, executable, rules, prior
real save, bridge, injector, clean source, and both projected runtime trees are
unchanged. Product and fixture tree SHA-256 values remained
`2DA668E0402856F0D441FF0B86D330EB6FD96BC327CE179770F2A6EB4825808D`
and `3D39A6EE3CCE98464FFE2A4C3DAC97AB501A0679E60E6C9BACF5DFCC3B41BC5B`.

## Distinct next step

The histogram live already proved that the selected loader callback
`0x88B480` executed once and published state 2. This seed attempt supplied no
new evidence that would justify another timeout-only run. The next live must
instead use the selected-task-to-scheduler-consumer correlation seam now
present after `0644d46`: retain the selected D7 task identity and compare it
against each `RBX` at consumer `0x3B9DEA7`, recording match count, first/last
state, reference count, callback presence, thread, and QPC. Only after that
distinct observation resolves the missing task flow should a new exact-source
canonical-seed attempt be frozen.
