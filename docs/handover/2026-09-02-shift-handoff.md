# 项目交接（2026-09-02）

> 交接目的：在当前执行者离岗前，给下一位执行者一份可直接恢复工作的事实账本。本文只记录已经取得的证据和可执行的下一步；`static-ready`、`fixture-live`、`production-live primitive` 与 `complete` 不混用。最后更新：主线 `7401613`。

## 0. 快速结论

| 工作包 | 当前状态 | 已完成边界 | 尚未闭环 |
| --- | --- | --- | --- |
| 宣传工具 | `complete / released` | 已拆到 `Z:\workspace\xar_promo_toolchain`，GitHub 独立仓库与 `v0.1.0` Release 已发布 | 后续版本需求另开工作包；不要把外部平台上传误写成已完成 |
| 天朝二期 | `static-ready + native-readiness RED + not-live` | loader 静态 CFG/指令边界、一次 exact-build loader 运行证据、NO-GO 诊断均已落盘 | 取得 callback/node 的可观测 native 入口并完成 paused/live 验收；当前不能宣称正式发布 |
| G2 | `production-live read-only primitive / GEN-034 unresolved` | paused exact-build 四个窄域只读 primitive、truce evaluator call-site contract、离线失败 seam 已固定 | `evaluated_days` live 结果、war-bound/策略/typed action/postcondition；不能执行 surrender/white-peace/enforce mutation |
| open_kaishek | `main` clean；schema/preflight 证据持续增加 | `is_acclaimed`、`can_be_acclaimed` 均已合入并通过 focused CI，均 `certified=false` | 不得把离线 parser/validator 预验当作 CK3 native/runtime 或 production readiness；`ACCOLADE` scope 仍是条件性后续项 |

交接材料索引：[`audit-2026-09-02.md`](audit-2026-09-02.md)、[`2026-09-02-g2-open-kaishek-handoff.md`](2026-09-02-g2-open-kaishek-handoff.md)、以及本文件。前两份是早于 `fefdb6d` 的事实快照；本文件与日报/周报的最新追加以 `7401613` 为准。

## 1. 当前主线与发布锚点

- 父仓库远端：`https://github.com/XenoAmess/ck3_eternal_recurrence.git`
- 本交接快照父仓库主线：`7401613`（交接索引刷新；phase2 dispatch 实现为 `fefdb6d`，报告收口为 `c38ede1`）；提交前先 `git fetch origin master`，若远端前进只做 fast-forward/rebase，不在用户脏工作树操作。此前交接提交链为 `0c9c43a` → `547c7ac` → `8d79ae2` → `fefdb6d` → `c38ede1` → `a922413` → `1821d36` → `8c17e92` → `7401613`。
- 用户原工作树 `Z:\ck3_mod_rewrite` 是 detached 且有用户现场改动（快照 `236dd32`）；禁止 reset、checkout、清理或覆盖。继续工作使用独立 clean worktree。
- 正式宣传工具仓库：`https://github.com/XenoAmess/xar_promo_toolchain`，本地 `Z:\workspace\xar_promo_toolchain`，`main` 与远端一致，`v0.1.0` 已有 wheel/sdist/SHA256SUMS。无需重复发布。
- `open_kaishek`：`Z:\workspace\open_kaishek`，当前 `main`/`origin/main` 为 `759199b`；保持少分支，临时分支完成后立即合并/删除。

## 2. 天朝二期：可直接恢复的事实

### 已取得

- exact CK3 build：`1.19.0.6`；EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 最近一次 live recheck：
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\phase2-live-recheck-20260902\artifacts-a89282d-f20-loader\runner-report.json`
  ，SHA-256 `187E1A438F0DCDE838BAC1AF02AAB878393BBAF999D704E3C9F2D843627FBBA9`。
- 结果是 `RED / loader_stage_timeout`，原因 `database_callback_stall`；仅观察到 `CGameConceptTypeDatabase`（441 ms）和 `CJominiLoadScreenDatabase`（9 ms），`PostInit=0`、`fatal=0`、退出清理全绿。该结果不证明 callback 语义已知。
- 静态 CFG 合同已在 `7ff9ca1` 合入：
  `ck3_autonomous_player/native_bridge/research/phase2_loader_callback_cfg_v1_abi.json`、对应 extractor/test，以及
  `docs/ck3-native-ai/phase2-loader-callback-cfg-2026-09-02.md`。
- callback probe NO-GO 说明：没有可复用的 debugger/硬件断点/loader 专用捕获入口；详见
  `docs/ck3-native-ai/phase2-loader-callback-probe-no-go-2026-09-02.md`。
- 最新静态 dispatch-window 增量已在 `fefdb6d` 合入：窗口
  `[0x3B9AB50,0x3B9AB93)`（67 bytes，14 instructions），保留两条 null CFG edge 与 8 个 direct callers；输出
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-boundary-next-20260902.json`，SHA-256
  `D2E0677813EC641DB77F0F8F81ECB6F57F611254A8A183A77776465B24424295`。focused static checks `6/6 + 4/4` GREEN；仍不代表 runtime callback 或 loader readiness。

### 下一步（仅一个最小入口）

1. 先对现有 frozen exact-build/source 做 `open_kaishek` OfflinePreflight；保留 preflight JSON 与 SHA。
2. 仅补 loader callback/node 的 source-symbol、ABI/vtable、线程/生命周期中一项可验证证据；dispatch-window 静态 patch 已由 `fefdb6d` 合入，下一入口直接转为 private paused exact-build observation。
3. 若没有新证据，记录 NO-GO 并停止；不要再次运行同一 loader timeout，不要猜 offset，不要改 public bridge/ABI/readiness。
4. 只有 callback 观测闭合后，才安排下一次 paused CK3 验收。当前不得宣称“天朝二期正式发布”。

## 3. G2：可直接恢复的事实

- fresh exact-build paused artifact：
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`，SHA-256
  `4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`。
- 快照身份：`native:3/rev4`，date `53223936`，CharacterID `29829`，WarID `50331699`，opponent `36769`；同帧 terms 双读一致，四个窄域 ready；`evaluated_days` 缺失，truce/decision/action 仍 false，无写入。
- `580f54f` 固定 `CAddTruce` evaluator call-site contract；verifier 一次结果：`exact_build=1 evaluator=1 call_sites=2 read_only=1`。合同 SHA-256：`55E5203647D2D0D0F017E990CBB736F42E306EFEE1269D7918DF39735A812799`。
- 私有 test-only truce failure seam 源提交 `6073381`，父仓合入 `8b6d1d6`；focused MSVC 测试通过，但 full CTest 的 15 个既有 baseline RED 不因本 seam 重新解释。
- campaign-dominance 静态 bounded scan 已明确 NO-GO：现有仅有 war-score/army/siege 等单帧 primitive，无 exact provider/RVA/call-shape；`GEN-034` 继续 unresolved。

### 下一步（优先级顺序）

1. 只做一次新的 paused exact-build private evaluator input/result（或 test-only pre-reset capture），并先跑 open_k 预验。
2. 若仍拿不到 live `evaluated_days`，保留失败 artifact，更新 blocker ledger，停止扩 public wire/readiness。
3. 在 `evaluated_days`、expiry、war-bound、decision/action/postcondition 全部有证据前，不执行或声称 surrender/white-peace/enforce；不重复旧 timeout。

## 4. open_kaishek：已发布能力与边界

- `is_acclaimed`：主线 `638f4c0`；preflight artifact SHA `D48913E0F4A831B0220EE2A818393CB3AA42B88D8B976097CF9652DEF30FFC73`；JAR SHA `D1341CD872D07E8081A4E53040655C420FB4A8EEDD24DC5DE616761CDFF068A2`。
- `can_be_acclaimed`：主线 `759199b`；preflight artifact SHA `503BA9C9F7D49E4154BC6B0FD29E763A59FD1AAC1BA3AED24767C29DC4ABE409`；JAR SHA `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`。
- 两个 descriptor 都是 `CHARACTER / TRIGGER / BOOLEAN`、零参数、`certified=false`；parser/validator/CLI focused 验证和 CI 均通过，IR/runtime/CK3/save/network 均明确 skipped/false。
- `has_accolade_parameter` 静态审阅已闭合 native 地址与参数形状，但要求新增 `ACCOLADE` scope 到 profile-api/runtime enum；目前不能降级成 `THIS`/`CHARACTER`，因此暂不实现。

### 预验规则

任何 CK3 验收步骤，先固定 source commit/build identity，再运行 open_kaishek OfflinePreflight，并保存 JSON/SHA；预验成功只说明离线 schema/语法边界，不能升级 parent 的 native/live readiness。

## 5. 报告、分支与 429 规则

- 日报：`docs/autonomous-agent-progress/daily/2026-09-02.md`；周报：`docs/autonomous-agent-progress/weekly/2026-W36.md`。新证据当场追加，必须带 artifact 路径、SHA、commit、CI、readiness 标签和遗留项。
- 最近父仓 Official Runner CI（截至快照）中 `7f31580` 对应 run `33592554247` SUCCESS；`fefdb6d` 对应 run `33593818448` SUCCESS；`1821d36` 对应 run `33597755214` 在交接时 `in_progress`。若远端已有更新，只查一次并记录结果。
- 每个工作包只做一次必要验证，完成即提交主线并推送；少分支、早合并。不要为了“清理”删除用户指定保留的构建目录或现场数据。
- 子进程遇到 HTTP `429`：直接复用原任务线程/工作树继续同一个 bounded 包，保留已有证据；不要把 429 当失败，不要从头重复无变化验证。规则已写入 `AGENTS.md` 与 `docs/branch-management.md`。

## 6. 交接执行清单

```text
[ ] 在 clean integration worktree fetch/rebase origin/master
[x] 确认 phase2/static-next 的 dispatch-window patch 已由 `fefdb6d` 合入，工作树 clean
[ ] 若做 G2 新入口，先 open_kaishek preflight，再做一次 paused/private evaluator capture
[ ] 任何新结果追加 daily/weekly，并带 SHA + readiness 边界
[ ] focused test 一次；通过后 commit + push master
[x] 更新本交接文档的“当前主线”commit 和时间
[ ] 不触碰 Z:\ck3_mod_rewrite 用户脏工作树，不重复旧 CK3 timeout
```

## 7. 明确的停止条件

若 callback 观测、G2 `evaluated_days` 或 exact-build provider 证据无法在现有工具/权限下取得，保持当前 NO-GO/未闭环标签，留下失败 artifact 和下一入口即可。不要用静态合同、ACK、schema、单场 fixture 或 CI 绿色替代真实 CK3/live 证据。

## 8. 2026-09-03 continuation addendum

### 双版本天朝二期宣传片

用户已明确要求人物版与制度群像版都作为正式交付物，二者分别维护导演稿、项目配置、authoring claims、候选片、审片、导出和 SHA-256。权威入口为
`docs/phase2-promo/README.md` 与 `phase2-dual-cut-production.md`；目标文件分别为
`zhongguo-361-phase2-character-led.mp4` 和 `zhongguo-361-phase2-institution-led.mp4`。

两版静态制作链和 builder 测试均已通过，但真实素材仍为 `0/8`，两个 MP4 均不存在。正式 TTS/渲染前必须再次执行宣传工具
`git fetch origin main --prune` 并确认 clean `HEAD == origin/main`；当前可写 fresh clone 已固定到
`57c42fca13ea459432c1caf76e069a1fbccf602c`。大体积媒体按约定落在外部 `artifacts/demos/YYYY-MM-DD/`，不塞进 Git 的 `docs/`。

### CK3 启动边界

在同一 `1.19.0.6`/EXE SHA-256 环境中，项目副本、Steam 库副本、`-gdpr-compliant`、`nographics` 以及游戏根目录 cwd 的裸启动都在
`ck3+0x1DABD89` 之前崩溃；无 mod、无 bridge 也可复现。最新 minidump 的故障指令为
`movsxd rdi, dword ptr [r14+0x4c]`，异常线程 `r14` 为无效小值；这不是 mod/bridge 证据。完整转储和每次尝试在
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\`，详情见 `docs/phase2-promo/live-startup-blocker-2026-09-03.md`。

### G2 与 open_kaishek

G2 slot-23/truce 定向 Python 回归为 `28 passed + 4 subtests`；Steam-library exact-build residual RTTI 离线提取为 GREEN，唯一 index-7
路径仍是 `hidden_effect → attacker Context → expected CAddTruceEffect<0>`，但 `evaluated_days` 仍必须做一次真实 paused/live 验证。
open_kaishek 可写同步 clone `81109e46` 的 Maven 全量测试在离线缓存下通过；完整 ZhongGuo 语料仍有 `172255 UNKNOWN_OPCODE`，保持
`certified=false`，canonical checkout/push 不能虚报为完成。

### 2026-09-03 06:39 open_kaishek 语料边界复核

使用同步 clone 的 CLI 对当前 `mod_zhongguo_style` 做了一次独立 corpus/语义分层检查：`corpus --require-corpus` 对 75 个源文件全部解析通过（`files=75, parsed=75, errors=0`，corpus SHA-256 `28e681358558f5e975fae911bf5ddf54eacb3c95dac3133852eaaeca6425c284`）；同一输入进入 `preflight --root` 后，parser 仍为 GREEN，但 1.19.0.6 profile validator 为 RED，`172255 UNKNOWN_OPCODE`，命令退出码为 1。该结果确认“语法可读”与“完整语义兼容”是两个独立门槛；本次没有修改语义表，也没有把 `certified` 升级。

报告回执：`_runtime/open-kaishek-zg361-corpus-latest.json` SHA-256 `23932F820036BC6879A2F12207F043BA85D96A2199D3A5497926EC540A29F765`；`_runtime/open-kaishek-zg361-preflight-latest.json` SHA-256 `1632824AB6C18FC0258A644B4F814403ADD6C4A868308AE56E9AAF87D58D617B`。

### 2026-09-03 06:51 Phase2 seed preflight receipt

Using the clean static freeze `165b47742fd05ff3713b8be4452711002328d57d`, source archive SHA-256 `77AA3E30F1C20763576DBEAE71B1C7451CFD63A15FB53A46FC58A373D72338E8`, synchronized `open_kaishek` commit `81109e46fce0c9b5efee49398f7411f772b1cfd9`, and the guard-on bridge build, the corrected no-launch preflight completed `GREEN / preflight-ready`.

Receipt: `_runtime/phase2-seed-20260903/artifacts-preflight-current-03/preflight.json`; SHA-256 `9057F967CFE97036AD4E3918C2640892371EBB006BBADDE18EE36DA7A4CABE2E`.

The receipt explicitly records `ck3_launch_attempted=false` and `seed_ready=false` with `seed_contract_status=blocked_seed_generation_required`. Source/archive equivalence, external dependencies, bridge, static preflight and production projection are green. The optional `open_kaishek` nested validator remains `certified=false` because the full 75-file corpus still reports `172255 UNKNOWN_OPCODE`; parser coverage remains `files=75, parsed=75, errors=0`. This is a valid preflight receipt, not live CK3 evidence and not a video export.

### 2026-09-03 06:55 documentation publication boundary

The updated handover, daily/weekly reports, and dual-cut production documents are present in the integration worktree. A scoped commit/push was attempted but the managed worktree denied `.git/worktrees/_root-promo-split-20260902/index.lock`, and the environment has no usable Git credential-manager/TTY. Therefore remote publication is not claimed; no reset, checkout, or cleanup was performed.

### 2026-09-03 07:02 release/static integrity recheck

`validate_static.py` is GREEN (40 option keys, 5 custom loc, 88 modifiers, 9 languages). `build_release.py --check` is GREEN with 86 files and a deterministic manifest/ZIP; `build_vivhite_release.py --check` is GREEN with 27 files. White-Qi manifest/ZIP SHA-256 values are `17EE1D49AA292C26E32025FBEB87C52DB3A2C94C488D378EEC4D3F2DD22CC0F0` and `B5D7F276C128878AE3F6A7F28110840515F7CE585FC6BF2E3CB998D73B460C08`. These checks verify source/release integrity only and do not promote CK3/live or promo-video readiness.

### 2026-09-03 07:03 current-tree acceptance preflight

With the Steam-library exact-build executable, isolated user directory, workshop cache, and guard-on bridge/injector explicitly bound, `run_zhongguo_acceptance.py --preflight` returned `ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN`. CK3 was not launched and no footage was produced; this is parameter-bound static acceptance evidence only.

### 2026-09-03 07:07 Phase2 preflight after G2 capability sync

The bounded no-launch seed preflight now binds open_kaishek commit `981c79388a07e447b18f8e4472a16fd65e28c083` and returns `GREEN / preflight-ready`, with `ck3_launch_attempted=false`. Receipt `_runtime/phase2-seed-20260903/artifacts-preflight-open981-current-07/preflight.json` has SHA-256 `4D22CA2B43ABF75D3D895BB26C2EE8183909E711337C495F9AE54A5A45948DDB`. The nested full-corpus validator remains `172255 UNKNOWN_OPCODE` while parser coverage is GREEN; seed/live/video readiness is unchanged.

The writable open_kaishek clone is clean and two commits ahead of `origin/main`; remote push is still unavailable because the environment lacks a usable credential-manager/TTY.

### 2026-09-03 07:10 replayable open_kaishek handoff

The two local sync commits (`81109e4`, `981c793`) are preserved for later canonical application. Patch: `artifacts/open-kaishek-sync/2026-09-03/0002-g2-truce-capability-sync.patch`, SHA-256 `24C6260B67DB2811AD4F278659690C27B99260D17A56BED1DA2929B5D32849CF`, 107,588 bytes. Git bundle: `artifacts/open-kaishek-sync/2026-09-03/open-kaishek-main-981c793.bundle`, SHA-256 `30FCA309D8C9F4954DE1A7F101DD9CCE0FC0513D3C1080FDEBD02D5793115588`, 17,057 bytes. These artifacts do not claim remote push success.

### 2026-09-03 07:13 G2 contract verification

The open_kaishek production compile succeeded. Full Maven tests remain blocked by local dependency-cache ACL/missing-parent-POM errors, so they are not called GREEN. An independent Java smoke assertion passed for `game.command.query-g2-truce-evaluated-days-v1`, covering the required fields, same-frame double-read and expiry boundaries, read-only behavior, and explicit `nativeCertified=false` / `runtimeCertified=false`.

### 2026-09-03 07:16 promo tool freshness gate

`git fetch origin main --prune` completed in the writable fresh promo-tool clone; it remains clean with `HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`. No formal TTS/render/export process was started because real CK3 footage is still unavailable.

### 2026-09-03 07:20 dual-video delivery index

Both mandatory Phase2 cuts are now explicitly indexed in `docs/phase2-promo/dual-video-delivery-status-2026-09-03.md`: character-led and institution-led, each with its own output name, claims ledger, review path, and export boundary. The available old fixture was checked read-only and correctly returned `RED / footage_pending`; it did not start CK3 or FFmpeg and produced no media. The two target MP4s remain absent because current CK3 launch evidence still ends in the pre-loader crash.

### 2026-09-03 07:22 G2/open_kaishek compatibility record

`docs/ck3-native-ai/g2-truce-open-kaishek-sync-2026-09-03.md` now records the exact cross-project binding for `game.command.query-g2-truce-evaluated-days-v1` at open_kaishek `981c79388a07e447b18f8e4472a16fd65e28c083`. This is a static compatibility contract only; native/runtime certification remains false pending one paused exact-build evaluator artifact.

### 2026-09-03 07:24 G2 focused regression

Using the project-standard `PYTHONPATH=ck3_autonomous_player/src`, the bounded G2 truce/preview suite passed with `21 passed, 12 subtests passed`. The only warning was the known pytest cache ACL warning; the earlier collection error was caused by an omitted import path and is not a code failure.

### 2026-09-03 07:28 project static validation

`tools/validate_static.py` passed with `LOC VALIDATION OK` and `STATIC VALIDATION OK` (generated parity, BOM/loc, mechanics/AI, release allowlist/assets). This is static-ready evidence only; it does not close the CK3 live or dual-video gates.

### 2026-09-03 07:30 dependency freshness

The promo-tool fresh clone fetched `origin/main` successfully and remains clean at `57c42fca13ea459432c1caf76e069a1fbccf602c`. The open_kaishek clone also fetched successfully and remains clean at local `981c79388a07e447b18f8e4472a16fd65e28c083` versus `origin/main` `0390b9a959fa1a59a968000ed49e827a03b8d4e4`. No external dependency changed.

### 2026-09-03 07:31 root G2 binding

The root `raiktor_surrender_truce_contract.py` now exposes descriptive constants matching the open_kaishek G2 profile capability, profile ID, and commit. The focused test passed with `6 passed, 12 subtests passed`; this is a compatibility binding only and does not promote native/runtime readiness.

### 2026-09-03 07:33 G2 regression after binding

The complete truce/preview focused set passed after the binding change: `22 passed, 12 subtests passed` (one known pytest cache ACL warning). No live readiness bit changed.

### 2026-09-03 07:35 G2 public bridge export

The frozen open_kaishek capability/profile/commit identities are now exported from `xar_autoplayer.bridge`; the import smoke returned `G2_OPEN_KAISHEK_PUBLIC_EXPORT_GREEN`. This is still a descriptive compatibility surface only and does not create a native query or action path.
### Current-state override (2026-09-03)

The early snapshot near the top of this handover predates today's sync. For current execution, use the later entries and `docs/ck3-native-ai/g2-truce-open-kaishek-sync-2026-09-03.md`: the writable open_kaishek branch is `981c79388a07e447b18f8e4472a16fd65e28c083`, while `origin/main` is `0390b9a959fa1a59a968000ed49e827a03b8d4e4`. The promo-tool freshness entry likewise supersedes older tool revisions.
### 2026-09-03 07:36 correctly bound ZhongGuo preflight

The acceptance preflight was rerun with `XAR_CK3_EXE` bound to the Steam-library exact-build executable and the guard-on bridge/injector. It returned `ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN` for CK3 `1.19.0.6`, expected EXE SHA, and desktop `2560x1440`. This remained no-launch static evidence and produced no footage.
### 2026-09-03 07:39 G2 generic war-bound successor seam

The cold-map VFS observer, guarded retry, and normal-desktop preflight contracts passed (`6 passed`, one known pytest cache ACL warning). The observer is still `static-ready-no-launch`; its next use is a bounded A/B live capture after a real startup-environment change, not another seventh guard or repeated blind launch.
### 2026-09-03 cross-project acceptance coverage

The open_kaishek coverage, workshop acceptance, Phase2 seed runner, and promo-runner plumbing tests passed with `43 passed, 8 subtests passed`. This is no-launch contract evidence only; it does not create CK3 footage or final video media.
### 2026-09-03 07:42 G2 public export regression

The root truce contract test now asserts that `xar_autoplayer.bridge` exports the same frozen open_kaishek binding; result `7 passed, 12 subtests passed` (one known pytest cache ACL warning).
## 2026-09-03 continuation checkpoint (08:08)

- 天朝二期双片：人物版与制度群像版均已落盘导演稿、独立配置、authoring ledger、制作包和独立 runbook。宣传工具 fresh clone 已核对 `HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`。两版 authoring/static 回归均 GREEN，但真实 CK3 素材仍为 `0/8`，目标 MP4 尚未生成；启动崩溃仍是唯一媒体硬阻塞。
- 双片 runbook：`_runtime/phase2-dual-runbooks-20260903-0800/character-runbook.json`（`RED / footage_pending`，SHA-256 `55E2751FBC8408682B04251C3706928A2C78B9B70F61D11D3D6C829DC572E408`）与 `institution-runbook.json`（`RED / footage_pending`，SHA-256 `6A3FD533B0656722CF8296224A286586F5AF8B568ECDA6C7B9B3A157007BF2BF`）。
- G2/open_kaishek：新增活动类型 schema RED 记录；parser GREEN、validator RED（172,255 个 `UNKNOWN_OPCODE`，集中于 `common/activities/activity_types/zg361_jingcha.txt`）。没有猜测性 allow-list 或运行时能力晋级；下一步是 exact-build 只读活动 schema/evaluator 证据。

## 2026-09-03 verification checkpoint (08:28)

- G2 truce/preview/scoreboard focused tests: `16 passed, 12 subtests passed`; `tools/validate_static.py`: GREEN；`build_release.py --check`: `86 files`, deterministic manifest/ZIP GREEN.
- Promo-tool fetch again confirmed clean `HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`. No target MP4 appeared; CK3 footage remains `0/8`.

## 2026-09-03 startup A/B checkpoint (09:02)

- Isolated CK3 launch with `-noWorkshop` reproduced the same `C0000005` at `ck3+0x1DABD89` before loader/database. Crash receipt and hashes are in `docs/phase2-promo/live-startup-probe-no-workshop-2026-09-03.md`.
- This rules out Workshop as the sole cause for the current crash; no additional guard was added and no seed/footage was created.

## 2026-09-03 userdir argument checkpoint (09:08)

- The same isolated probe with `--userdir=<path>` reproduced `ck3+0x1DABD89`; short versus equal-sign userdir syntax is not the cause. No seed or footage was created.

### 2026-09-03 08:35 open_kaishek push and Maven verification

The open_kaishek compatibility branch was pushed successfully to `origin/main` at
`981c79388a07e447b18f8e4472a16fd65e28c083` (base `0390b9a`). Full Maven tests passed
using the isolated repository `Z:/ck3_mod_rewrite/_runtime/m2-openkaishek`:
`125 tests, 0 failures, 0 errors, 0 skipped`. Refreshed patch and bundle hashes,
including the push receipt, are in
`artifacts/open-kaishek-sync/2026-09-03/open-kaishek-main-981c793-receipt.json`.
No activity opcode or allow-list was guessed; this remains a read-only compatibility
sync and does not promote CK3 native/runtime readiness.

## 2026-09-03 open_kaishek sync checkpoint (08:35)

- Compatibility branch push completed: `HEAD == origin/main == 981c79388a07e447b18f8e4472a16fd65e28c083` after advancing remote `main` from `0390b9a959fa1a59a968000ed49e827a03b8d4e4`.
- Isolated-repository Maven test run passed all `125` tests with zero failures/errors/skips. The two Zhongguo business-postcondition fixtures and seven CK3 1.19.0.6 schema fixtures are parser/validator `GREEN`, while IR/runtime are deliberately `SKIPPED` and `ck3_started=false`.
- Regenerated artifacts: `artifacts/open-kaishek-sync/2026-09-03/0002-g2-truce-capability-sync.patch` (SHA-256 `0AB47A75A830FB9861009D20E252B6F93FF0D8A7355CB4535E4B9FE9010957EE`) and `open-kaishek-main-981c793.bundle` (SHA-256 `DCE6AF147692A8F9873D1D99CFE42D57D59D6C87B4596A3E60BF2F1BE47804E3`; bundle verify passed). Full receipt: `artifacts/open-kaishek-sync/2026-09-03/open-kaishek-main-981c793-receipt.json`.
- Scope remains static compatibility only: no CK3 activity opcode/allow-list guess, native evaluator claim, or live launch was introduced.

## 2026-09-03 09:20 Steam entry probe

The running Steam client was invoked through `steam.exe -applaunch 1158310` and
monitored for 35 seconds. No CK3/dowser child appeared and no new crash directory
was created, so this closes only the alternate Steam entry hypothesis as a
no-launch harness result. It did not produce loader readiness, a seed, footage, or
any store/purchase/payment action.
