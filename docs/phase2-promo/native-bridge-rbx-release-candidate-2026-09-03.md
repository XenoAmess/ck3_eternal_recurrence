# Phase2 startup-guard bridge candidate (2026-09-03)

This record describes an independent, no-launch Release build prepared for a
serialized exact-build CK3 check. It is a candidate only: it does not replace
the existing `freeze165b` bridge and it does not promote any live capability.

## Candidate identity

- Build directory: `Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903`
- Source tree: `ck3_autonomous_player/native_bridge`
- Native-tree revision: `e4e8b6f90be60a7cfa3b155083b9eb21d1b7791b`
- Native source fingerprint (278 files):
  `84E0E44424744BE3385D71CE4ED20047F62B0E15ACA3932D2F627A79C08D6053`
- Game build admitted by the static record: CK3 `1.19.0.6`, executable
  SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

The source fingerprint covers `CMakeLists.txt` and every `.cpp`, `.hpp`, `.h`,
and `.c` file below `include/` and `src/`, using the same algorithm as
`native_bridge/tools/build_fresh.ps1`. No native source was dirty when the
candidate was recorded.

## Build configuration

The build used a fresh Ninja directory, CMake `4.3.1-msvc1`, Ninja `1.13.2`,
CTest `4.3.1-msvc1`, and MSVC `19.51.36248.0` x64. The exact cache is retained
at `Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903\CMakeCache.txt` and copied
to the artifact directory; its SHA-256 is
`12836F43BEE36526D27209B30A5BDF12AC6C07DD636B7B14224D6F296D09C940`.

Enabled options:

- `XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=ON`
- `XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=ON`
- `XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=ON`

Intentionally disabled options:

- `XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1=OFF`
- `XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=OFF`

The resulting install order is the existing four-guard containment chain,
followed by the widget and RBX caller-local guards:

`Particle2Null -> Particle2Consumer -> DX11Draw -> LocalizeCurrentRoot -> WidgetNullFlag -> RbxNullCall`.

## Static evidence

The bridge built and linked successfully (`444/444` Ninja steps). The Ninja
dependency gate is green for both `ck3_11906.cpp.obj` and
`ck3_11906_adapter.cpp.obj`; each records `ck3_11906.hpp` (`#deps 5` and
`#deps 18`).

Artifacts:

- `xar_ck3_bridge.dll`, 2,260,992 bytes,
  SHA-256 `99BC4656D8258789803046A73B2B7798EAAA9C72B586D91CD28A8751365A89E9`
- `xar_ck3_bridge_injector.exe`, 39,936 bytes,
  SHA-256 `10D0511D159AF9187FADF615EC2CBF69C28BC27A2FC32D1BF8CAA5C28CD37A27`

CTest was run in two forms:

- The unfiltered 88-test suite is retained as **RED baseline drift**: 73 passed,
  15 failed. Ten failures are current source-contract/hash drift and five are
  older particle2/DX11/localization successor fixture/hash contracts. No source
  contract or frozen fixture was changed to hide these failures.
- Excluding exactly those 15 known stale contracts, 73/73 passed.
- The focused widget/RBX guard tests passed 2/2.
- The four corresponding Python guard-contract tests passed 18/18.

Full command output is retained under:
`artifacts/g2/2026-09-03/phase2-startup-guards-rbx-release-20260903/`.
The machine-readable summary is `candidate-manifest.json`; the cache,
dependency gate, filtered CTest, focused CTest, and Python logs are alongside
it.

## Boundary and handoff

This is `static-ready-no-launch`, not `fixture-live` or `production-live`.
The task intentionally did not start CK3, inject the DLL into CK3, alter a
profile, issue gameplay commands, or replace the `freeze165b` artifact. A
later operator may use the recorded DLL and injector in one serialized exact-
build run after checking the current CK3 process/slot state and preserving its
report separately.
