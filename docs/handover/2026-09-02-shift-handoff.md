# 项目交接（2026-09-02）

> 交接目的：在当前执行者离岗前，给下一位执行者一份可直接恢复工作的事实账本。本文只记录已经取得的证据和可执行的下一步；`static-ready`、`fixture-live`、`production-live primitive` 与 `complete` 不混用。最后更新：主线 `a922413`。

## 0. 快速结论

| 工作包 | 当前状态 | 已完成边界 | 尚未闭环 |
| --- | --- | --- | --- |
| 宣传工具 | `complete / released` | 已拆到 `Z:\workspace\xar_promo_toolchain`，GitHub 独立仓库与 `v0.1.0` Release 已发布 | 后续版本需求另开工作包；不要把外部平台上传误写成已完成 |
| 天朝二期 | `static-ready + native-readiness RED + not-live` | loader 静态 CFG/指令边界、一次 exact-build loader 运行证据、NO-GO 诊断均已落盘 | 取得 callback/node 的可观测 native 入口并完成 paused/live 验收；当前不能宣称正式发布 |
| G2 | `production-live read-only primitive / GEN-034 unresolved` | paused exact-build 四个窄域只读 primitive、truce evaluator call-site contract、离线失败 seam 已固定 | `evaluated_days` live 结果、war-bound/策略/typed action/postcondition；不能执行 surrender/white-peace/enforce mutation |
| open_kaishek | `main` clean；schema/preflight 证据持续增加 | `is_acclaimed`、`can_be_acclaimed` 均已合入并通过 focused CI，均 `certified=false` | 不得把离线 parser/validator 预验当作 CK3 native/runtime 或 production readiness；`ACCOLADE` scope 仍是条件性后续项 |

交接材料索引：[`audit-2026-09-02.md`](audit-2026-09-02.md)、[`2026-09-02-g2-open-kaishek-handoff.md`](2026-09-02-g2-open-kaishek-handoff.md)、以及本文件。前两份是早于 `fefdb6d` 的事实快照；本文件与日报/周报的最新追加以 `96ab298` 为准。

## 1. 当前主线与发布锚点

- 父仓库远端：`https://github.com/XenoAmess/ck3_eternal_recurrence.git`
- 本交接快照父仓库主线：`a922413`（交接文档刷新；phase2 dispatch 实现为 `fefdb6d`，报告收口为 `c38ede1`）；提交前先 `git fetch origin master`，若远端前进只做 fast-forward/rebase，不在用户脏工作树操作。此前交接提交链为 `0c9c43a` → `547c7ac` → `8d79ae2` → `fefdb6d` → `c38ede1`。
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
2. 仅补 loader callback/node 的 source-symbol、ABI/vtable、线程/生命周期中一项可验证证据；优先复用 `phase2/static-next-20260902` 工作树已有 dispatch-window patch，先判断是否被 `7ff9ca1` 覆盖。
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
- 最近父仓 Official Runner CI（截至快照）中 `7f31580` 对应 run `33592554247` SUCCESS；`fefdb6d` 对应 run `33593818448` SUCCESS；`a922413` 的 CI 以 GitHub 实时状态为准。若远端已有更新，只查一次并记录结果。
- 每个工作包只做一次必要验证，完成即提交主线并推送；少分支、早合并。不要为了“清理”删除用户指定保留的构建目录或现场数据。
- 子进程遇到 HTTP `429`：直接复用原任务线程/工作树继续同一个 bounded 包，保留已有证据；不要把 429 当失败，不要从头重复无变化验证。规则已写入 `AGENTS.md` 与 `docs/branch-management.md`。

## 6. 交接执行清单

```text
[ ] 在 clean integration worktree fetch/rebase origin/master
[ ] 确认 phase2/static-next 的 dispatch-window patch 已由 `fefdb6d` 合入，工作树 clean
[ ] 若做 G2 新入口，先 open_kaishek preflight，再做一次 paused/private evaluator capture
[ ] 任何新结果追加 daily/weekly，并带 SHA + readiness 边界
[ ] focused test 一次；通过后 commit + push master
[ ] 更新本交接文档的“当前主线”commit 和时间
[ ] 不触碰 Z:\ck3_mod_rewrite 用户脏工作树，不重复旧 CK3 timeout
```

## 7. 明确的停止条件

若 callback 观测、G2 `evaluated_days` 或 exact-build provider 证据无法在现有工具/权限下取得，保持当前 NO-GO/未闭环标签，留下失败 artifact 和下一入口即可。不要用静态合同、ACK、schema、单场 fixture 或 CI 绿色替代真实 CK3/live 证据。
