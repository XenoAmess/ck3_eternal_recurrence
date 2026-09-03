# 度假交接：天朝二期、G2 与 open_kaishek

**交接时间：** 2026-09-03 20:45（Asia/Shanghai）  
**工作树：** `Z:\ck3_mod_rewrite\_root-promo-split-20260902`  
**分支：** `integration/progress-20260902`

这份文档接续 [`2026-09-02-shift-handoff.md`](2026-09-02-shift-handoff.md)。本轮最后一项 CK3 实机轮次已经自然结束并完成清理；没有强制杀进程，也没有再开启下一轮。工作区有大量既有的并行代理改动和 disposable `_runtime` 产物，**不要**用 `git reset --hard`、全仓清理或 `git clean -fd` 收拾现场。

## 一句话结论

天朝二期还没有到可交付或可制作成片的阶段。当前最小的已验证二期入口是 53 文件 case-kernel（完整进图 GREEN）；加入当前 ABI safe-core 后的 55 文件组合也完整进图 GREEN。刚结束的 58 文件 B1（safe-core + B1 三文件闭包）在 1200 秒内一直停在“启动游戏中……”，主菜单 OCR 超时，属于 **pre-menu startup-time / harness RED**，不能写成 B1 功能已通过，也不能仅凭这一次把全部原因归咎于某一个文件。CK3 进程已确认退出，当前没有残留 CK3/python 测试进程。

## 当前工作清单

| 工作包 | 当前状态 | 下一项 | 预计交付窗口（接班人重新开始后） |
|---|---|---|---|
| 天朝二期代码/内容 | `static-ready`；53、55 文件组合有完整进图证据，B1 当前轮次未通过 | 以 safe-core 55 为基线，把 B1 effect 按真实依赖块继续拆小；每次只开一个 CK3，达到“选人并进入暂停地图”才记 GREEN | 每个小轮约 20–30 分钟；B1 根因未定位前不给全量 ETA |
| 两版最终宣传视频 | `footage_pending`，真实二期素材仍为 `0/8`，两份目标 MP4 均未生成 | 先取得 8 个 clean CK3 spans；随后再 fetch/pull 宣传工具主线、TTS、渲染、字幕审片、分别导出两版 | 素材齐后制作约 45–90 分钟，另需两轮人工审片；当前不能承诺日期 |
| 宣传工具 | 已满足“制作前更新”前置条件：`Z:\workspace\xar_promo_toolchain` clean，`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`（v0.2.1） | 正式 TTS/渲染前再次执行 `git fetch origin main --prune`，把 checkout SHA 写入两份 builder receipt | 工具本身已完成；等待素材 |
| G2 | **按用户要求暂缓**，不再扩展当前迭代 | 只有用户解除暂停后才恢复；恢复前先读 G2 专题和最新 schema boundary | 暂无 |
| open_kaishek | 兼容性同步已完成，`Z:\workspace\open_kaishek` clean，`main == origin/main == 15ab978f879ed4562aacb74dacdaee702fbce54b`；仍是 static-only | 恢复 G2 时重跑 Maven/fixture；不得把 parser/validator 结果写成 native/runtime readiness | 暂无 |

## 本轮最后一项实机结果（B1，已收束）

### 静态身份

- 规范候选：`Z:\ck3_mod_rewrite\_root-promo-split-20260902\_runtime\phase2-next-increment-b1-20260903\product`
- 规范 projection：`...\projection.json`，58 files / 7,858,198 B，文件 SHA-256 `20346BA3EDA3218BBEBCE3252ED955C0CA4ED4AD28E8D182681E2C12608E6359`
- strict preflight：`...\preflight.json`，SHA-256 `F9901D5971795EBE577D2F4E722CABC482E025907CD5BE4EAB3113DF4F0956A6`，状态 `GREEN_STATIC`
- 规范 source/materialized tree SHA：`E4EE07DE11317DBE12D44DD6659A4010CC5255CA2B9A9C858C423BB82FBEC92D`
- formal overlay SHA：`F171B3CA307A9CD35E5F2BC7E9E2785D4EA0C31D0DE6DBCE342E624A4A9D8A3D`
- 本次实际挂载的是等字节的 disposable product：`Z:\ck3_mod_rewrite\_runtime\phase2-next-increment-b1-closed-zh-20260903-r1\product`；probe report 中记录的 product tree SHA 为 formal overlay 的 `F171...`。后续不要把 report 的 product SHA 与 projection 的 source SHA 混用。
- 增量正好三条路径：
  - `common/scripted_effects/zg361_b1_runtime_effects.txt`，495,777 B，SHA `CDB388005FFEAC6D332380E910FBBF929F49871047E118D047C63B8751C001B4`
  - `events/zg361_b1_runtime_events.txt`，29,639 B，SHA `6576EA63F654D2321620A026471390F147B90719D98F69FEEA34F4C5779E8543`
  - `localization/simp_chinese/zg361_b1_l_simp_chinese.yml`，7,136 B，SHA `00320692C35E9ED6DDB0D02F9D1D988876F22AA72B966A3247EFD87F9ADAC938`

### 实机证据

- CK3 版本 `1.19.0.6`，buildid `23530548`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- probe：`Z:\ck3_mod_rewrite\_root-promo-split-20260902\_runtime\minimal-entry-probe-20260903\run_minimal_entry_probe.py`，脚本 SHA `F7DC208BF69F1B2E1F2BDAB81F718196493A15098378D5E6789123435655E333`
- artifact 目录：`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-next-increment-b1-closed-zh-full-entry-20260903`
- 报告：`report.json`，SHA-256 `41942EFCB595B5A1B134156075F9B454A40DA38700735986F42831A9CBC5D650`
- 开始 `19:54:30.955`，自然结束/清理 `20:14:36`，`duration_seconds=1205.343`（约 20 分 05 秒）
- report `result=RED`，错误是 `RunnerError: OCR timeout waiting for 新游戏`；所有 `main_menu/bookmark/start/gameplay/map/paused/candidate_mounted/game_state_ready` 均为 `false`，没有 `Frontend`、history 或 `In Game` marker。
- `timeout_01_main_menu.png` SHA `809879FCD5F45B31F96115065A2F99B3F33D7FAB929E2C76EE5CA7C58CBC624A`，画面仍是 CK3“启动游戏中……”加载页；不是协议弹窗或购买页面。
- debug.log SHA `C7BE685C24567B49419777E2AA18DE35DA8849CD6C4963483FE046C5D63451DE`；error.log SHA `3B96FDA043FCD18B502010F5677958D90B2C03B92B7E6EB9B4FCEA670A7B13C3`（1001 行）。匹配到的内容主要是 `set but never used`、`used but never set` 和两个 list-target 诊断；没有已知 material parser/unknown-opcode/invalid-scope 模式。它们不能被误写成“解析器已通过”，也不能单独证明是崩溃。
- cleanup：`ck3_running_after=false`、userdir 保留。当前轮次没有残留 CK3 进程。

分类要点：这是 **pre-menu startup-time / harness OCR RED**。截图和日志说明启动负载很重（最后推进到 error-suppression 与 database-dependencies 初始化），但 runner 在主菜单前超时，所以无法判断 B1 的功能语义是否已经可玩；下一位应把它当作“需要缩小/定位加载开销”的失败证据，而不是删除生产代码的理由。

## 已完成的可复核批次与耗时

| 批次 | 规模 | 实机结果 | 耗时 | 证据 |
|---|---:|---|---:|---|
| 53-file pure case-kernel（旧 lineage） | 53 files / 7,313,274 B | **GREEN**：主菜单、选人、开始、HUD、地图、暂停及三条 game-state marker | 300.656 s（约 5:00.656） | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-minimal-full-entry-20260903-r3\report.json`，SHA `AF6F671FFAB9CC38F96EA9446A276D81362274B75E813C403F3BEA51185BA883`；tree `BDB8D89162C1C4B01058A3987FE916BD0DDA16CBD67EDABB412ED9E3F0FD7265`；地图图 SHA `FCE77CF853CD68FBA4461A84000694CBCE66FEA4DB73EA3D552A70D41818F3B` |
| 55-file safe-core ABI | 55 files / 7,325,646 B | **GREEN**：同一完整进图门槛，cleanup GREEN | 688.087 s（约 11:28.087） | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-next-increment-safe-core-full-entry-20260903\report.json`，SHA `00DB2B83503F6AE66216925897E4394C5AFC32300602DFA9ED6A46700BD3D422`；tree/formal `3D96D527D0486944492010DB05DDC4EB50C7BB3777DFCDE4509CDE4E48659B7`（以 report/projection 为准）；地图图 SHA `91F61D2107B6B06BD4B8224A73F4F2D02FAA59FB03E8A03C0819A61456D2E4BE` |
| 58-file B1 closed-ZH（本轮） | 58 files / 7,858,198 B | **RED**：20 分钟仍停启动页，未到主菜单 | 1205.343 s | 上一节 report/screenshot/debug/error；这是当前失败 attempt，必须保留 |

另有旧 lineage 的 62-file `core+b1` 曾在约 60.124510 s 到达 Frontend/End loading of history，但它缺少当前 case-kernel、incident/manager value 闭包，不能与本轮 58-file 候选当作同一实验；它只能说明“B1 effect 本身曾在另一 overlay 中快速到达启动边界”，不能推翻本轮结果。

## 耗时规律与经验教训

1. **字节数不是启动时间的线性预测。** 53→55 只增加 12,372 B（+0.169%），但引擎 `Total startup duration` 从 246.185372 s 变成 595.536113 s（+349.350741 s），probe wall time 增加 387.431 s。safe-core 仍然是功能 GREEN；慢更像可达的 scalar/trigger 依赖、缓存和调度共同作用，不能把 +349 s 全归罪于四个新增文件。
2. **B1 的新增量确实集中在一个大 effect 文件。** 相对 safe-core 增加 532,552 B（+7.27%），其中 effect 占约 93.09%；本轮在 GUI 预加载后长时间处于变量索引和 database dependency 阶段。这足以要求下一轮做 effect 分块 A/B，但还不足以证明某个 block 是唯一根因。
3. **冷 profile 会放大波动。** 每轮 disposable userdir 都会重建 shader cache、GUI/数据库缓存，磁盘和多线程调度也不同；因此必须固定 EXE、工作目录、profile 模板、语言和 timeout，并同时记录引擎 `Total startup duration` 与 probe wall time。不要拿一次冷启动的墙钟差直接当作代码复杂度比例。
4. **入口层级必须分开写。** 进程创建、Frontend、`End loading of history`、选人后 HUD/地图/暂停、native paused snapshot、seed、生产 OODA loop 是不同门槛。只有本项目约定的“选人并进入暂停地图 + candidate mounted + 三条 game-state marker + 无 material error + cleanup”才可写 full-entry GREEN；observer heartbeat 缺失不能反推 CK3 没启动。
5. **依赖闭包比“文件数量”重要。** 53-file case-kernel 是两个文件的真实语义闭包；55-file safe-core 还包含 current values/triggers 的 ABI 替换。B1 的 3-file 增量只在 safe-core 基线上闭合；单独拿 effect-only 或 event-only 做的只能叫 parser smoke/定位实验，不能叫完整功能批次。B2 直接 owner 就至少需要 6 个文件，保守固定点约为新增 34 files，不能硬拆成五文件生产包。
6. **路径与哈希必须分层记录。** nested canonical projection、materialized source tree、formal overlay 和 probe 实际 disposable product 曾出现过“路径看似相同但 SHA 字段代表不同层”的风险。每次运行前写清绝对 candidate path、projection SHA、tree SHA、probe SHA；不要用旧的 `r1`/无简中副本覆盖新证据。
7. **失败证据不要抹掉。** r1 的 harness path error、r2 的 splash-only/incomplete、baseline51 的按用户要求中止、B1 的 pre-menu OCR timeout 都要保留并标明层级；不要为了让表格好看而改成 GREEN，也不要因理论风险大范围重写生产树。
8. **超时不是游戏硬限制。** 以前的 180 秒、30 分钟、1200 秒都是 runner 观察窗口，不是 CK3、Steam 或“11 GB 内存上限”。本轮 1200 秒到边界后让 probe 自己清理，证明长启动应先延长/拆分观察并保存证据，而不是猜一个系统上限。

## 接班人的第一轮操作建议（现在不要自动执行）

1. 先读 [`docs/phase2-promo/phase2-incremental-startup-batch-plan-2026-09-03.md`](../phase2-promo/phase2-incremental-startup-batch-plan-2026-09-03.md)、[`docs/phase2-promo/README.md`](../phase2-promo/README.md) 和工作区的 [`phase2-safe-core-next-domain-closure-2026-09-03.md`](../../../docs/phase2-promo/phase2-safe-core-next-domain-closure-2026-09-03.md)。确认没有 CK3 后，再做静态检查；不要重跑已证明的 53/55 基线。
2. 以 safe-core 55 为唯一当前 ABI 基线，先把 B1 effect 按完整 block/依赖边界拆成一个最小可解析增量；保留对应 event 与当前语言 loc。每个候选先跑 strict preflight，记录 projection、materialized、formal 三层 SHA。
3. CK3 槽位严格串行：固定 `1.19.0.6` EXE、已验证 profile/cache 和 probe 脚本；一次只跑一个候选，timeout 先用 1200 s。每 30–60 s 只读记录进程、debug.log、memory 和 marker；若自然结束，保存 report/screenshot/log hash，确认 `ck3_running_after=false` 后再开下一轮。
4. B1 若仍在 pre-menu 卡住，优先做 `values bodies=0`、仅 ip、仅 mg、triggers-only 或 effect block 二分的控制实验；这些是定位实验，不要直接改 canonical production 文件。若某个闭包达到 full-entry GREEN，再进入下一域（Incident 或 Manager）。
5. Incident 简中闭包（safe-core 基线 + 3 条增量）和 Manager 简中闭包（+4 条增量）已经静态物化，可作为后续候选；B2 的 stub 不可冒充生产功能。静态域清单中的 manifest/hash 以工作区 `docs/phase2-promo/phase2-safe-core-next-domain-closure-2026-09-03.md` 为准。
6. 视频路线保持两条独立交付：人物版与制度群像版都不能因另一版完成而自动签核。只有 8/8 clean CK3 spans、source review、字幕/媒体检查和 builder receipt 齐全后，才运行 TTS/render/export；制作前再次 fetch 宣传工具 `origin/main`。
7. G2 维持暂停。open_kaishek 的 15ab978 是明确的 activity-schema negative boundary；它的 RED 是覆盖缺口，不是 CK3 runtime 失败。恢复时先重跑 Maven/fixture 并更新本项目绑定，不要猜 activity opcode allow-list。

## 交接时的授权边界

- 可以在 CK3/Paradox 弹出协议或通知时按用户既有授权同意/关闭；右下角 Toast 可清理。
- **禁止**任何购买、付款、充值、商店下单或其他付费动作；看到购买/付款/商店语义立即停在安全按钮前。
- 不要把点击协议、启动成功或一场 fixture 当成 Phase2 完成；不要自动发布未审片视频。

## 现场核对清单

- [x] 当前 B1 round 自然结束，report/screenshot/log 已保存。
- [x] `ck3.exe` 与测试 python 进程均已退出；没有留下运行中的 CK3。
- [x] B1 RED 已写入日报；日报当前 SHA `6BB5444045810DA660601303AA2FF9C08F0FC391049E5035E0C52C878ABB2FD7`。
- [x] Phase2 evidence index 已收录 B1；JSON SHA `52BCE65035F7974083D104E19064477DD4A20755691AF58B79409C9120DFE3C3`，MD SHA `D06938791BC3F7D4EB19651FED5D344C629893C0A95DBC06D3F7857CE291BDB8`。
- [x] 宣传工具 checkout 已更新并与远端主线一致；没有启动 TTS/render，也没有生成占位 MP4。
- [x] G2 已按用户要求暂缓；open_kaishek 工作树 clean。
- [ ] 下一位接班人重新开始前，先确认工作区 dirty/untracked 清单，不要覆盖或清理上述 disposable artifact。

这就是本轮可以安全交出的边界：证据齐全、失败可复现、现场已收尾，但天朝二期全量、两部最终宣传视频和 native/production readiness 仍未完成。
