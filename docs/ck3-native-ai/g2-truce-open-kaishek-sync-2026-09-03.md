# G2 truce 与 open_kaishek 能力合同同步（2026-09-03）

本记录把 G2 的 `evaluated_days` 观测需求与 open_kaishek 的只读能力描述绑定起来。它是静态兼容性合同，不把离线 profile 或编译成功提升为 CK3 实机能力。

## 当前绑定

| 项目 | 值 |
|---|---|
| open_kaishek profile | `ck3-1.19.0.6-g2-truce-evaluator-v1` |
| capability | `game.command.query-g2-truce-evaluated-days-v1` |
| open_kaishek commit | `135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b` |
| 可回放 bundle | `artifacts/open-kaishek-sync/2026-09-03/open-kaishek-main-981c793.bundle` |
| bundle SHA-256 | `30FCA309D8C9F4954DE1A7F101DD9CCE0FC0513D3C1080FDEBD02D5793115588` |
| root public backend | `ck3-1.19.0.6-native-raiktor-surrender-truce-v1` |
| readiness | `static contract only; native/runtime certification false` |

## 字段与不变量

open_kaishek profile 与 root G2 truce public wire 共同要求以下最小观测语义：

- `owner_character_id` 与 `toward_character_id` 必须是不同角色；
- `evaluated_days` 只有在 `evaluated_days_observable=true` 时才可为非负值；
- 同一个 paused frame 必须完成两次 evaluator read 且结果一致；
- 不得从 `evaluated_days` 推导 `expiry_date_raw`；
- observer 只读，不能提交 termination/action 写入；
- 真实 ready 仍需要 exact-build paused artifact，不能由 schema、Java compile、ACK 或静态 smoke 替代。

root 侧现有 `raiktor_surrender_truce_contract.py` 继续负责 payload 的严格字段、session binding、paused/stability 和无 expiry 推断校验；open_kaishek profile 只描述跨项目能力边界，不绕过这些校验。

## 验证证据

- open_kaishek production compile：`mvn -o -ntp -Dmaven.test.skip=true package` 成功；完整 Maven tests 仍受本地依赖缓存 ACL/离线 parent POM 阻塞，未标记 GREEN。
- 独立 Java smoke：`G2_CAPABILITY_ASSERTIONS_GREEN game.command.query-g2-truce-evaluated-days-v1`，核对了字段、不变量、只读边界和 `nativeCertified=false` / `runtimeCertified=false`。
- root G2 Python focused suite 仍保持既有 GREEN；当前没有新的 paused live artifact，`evaluated_days` 不提升 readiness。

## 后续同步规则

任何一方改变 capability ID、字段、不变量、profile ID 或版本绑定时，必须同时更新另一方的合同与本文件，并重新生成 bundle/patch 与 smoke 证据。取得 exact-build paused evaluator artifact 后，才允许新增 production-live projector；在此之前继续保持 fail-closed。
## Bundle verification context

The Git bundle verifies successfully when checked from the open_kaishek clone that contains its prerequisite commit `0390b9a959fa1a59a968000ed49e827a03b8d4e4`; checking it from the unrelated root repository correctly reports the prerequisite as absent. The bundle itself is intact and contains `refs/heads/main` at `981c79388a07e447b18f8e4472a16fd65e28c083`.

## Root-side binding

`raiktor_surrender_truce_contract.py` now exposes the same capability ID, profile ID, and open_kaishek commit as descriptive constants. A unit test checks the exact values; these constants do not alter the existing paused/stability/expiry checks and do not promote native or runtime readiness.

The three constants are also exported from `xar_autoplayer.bridge`, and the public import smoke check passed with `G2_OPEN_KAISHEK_PUBLIC_EXPORT_GREEN`. This only makes the frozen compatibility identity available to consumers; it does not create a native query or action path.

## 2026-09-03 08:35 remote sync receipt

The compatibility branch was pushed successfully: `origin/main` now points to
`981c79388a07e447b18f8e4472a16fd65e28c083` (base `0390b9a`). An isolated Maven
repository was used to avoid the host cache ACL issue; the full test suite passed
with `125 tests, 0 failures, 0 errors, 0 skipped`. The refreshed patch and bundle
receipts are recorded in `artifacts/open-kaishek-sync/2026-09-03/`:

- patch SHA-256: `0AB47A75A830FB9861009D20E252B6F93FF0D8A7355CB4535E4B9FE9010957EE`;
- bundle SHA-256: `DCE6AF147692A8F9873D1D99CFE42D57D59D6C87B4596A3E60BF2F1BE47804E3`;
- `git bundle verify` passed when checked against prerequisite `0390b9a`.

This receipt covers only the two compatibility commits and the read-only G2
capability contract. No CK3 activity opcode or allow-list was guessed or changed;
native/runtime certification remains false pending the exact-build paused artifact.

## 2026-09-04 B3 companion-capability sync

The canonical open_kaishek main advanced from `15ab978` to
`135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b` to add the static, read-only B3
manager-governance capability descriptor. The G2 capability ID, profile ID,
required fields, invariants, and certification flags did not change. Root now
pins the newer repository identity so the cross-repository verifier remains
exact while `native_certified=false` and `runtime_certified=false` stay closed.

The B3 addition is a `CapabilityDescriptor`, not a Paradox opcode or an
open_kaishek runtime handler. Full Maven verification at the new commit passed
129 tests with zero failures/errors/skips; the rebuilt CLI JAR is 343,043 bytes
with SHA-256
`538FA5728329EEC0A7134E0DCC70804EA3406A14FD04E5FA0F2DB3853466667B`.
The current 295-file companion corpus remains parser GREEN (23,919,869 bytes,
SHA-256 `E01B4AFDB5021D4BFF4E77D149F0A0E2270350B83573E4E60011A3336B103B03`).
Its validator remains RED at the already documented bounded vocabulary-coverage
boundary; no schema suppression or readiness promotion was made.
