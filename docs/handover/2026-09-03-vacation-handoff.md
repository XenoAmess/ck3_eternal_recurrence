# 度假交接：天朝二期、G2 与 open_kaishek

**原交接时间：** 2026-09-03 20:45（Asia/Shanghai）

**接班执行更新：** 2026-09-04 02:45（Asia/Shanghai）

**工作树：** `Z:\ck3_mod_rewrite\_root-promo-split-20260902`

**分支：** `integration/progress-20260902`

这份文档接续 [`2026-09-02-shift-handoff.md`](2026-09-02-shift-handoff.md)。原交接时的 B1 实机轮次已自然结束并完成清理；接班后又严格串行完成 B1 诊断/正式 split、B2 r2 与 Incident/X r3 full-entry，所有真正启动 CK3 的轮次均已自然退出，当前无 CK3 残留。工作区有大量既有的并行代理改动和 disposable `_runtime` 产物，**不要**用 `git reset --hard`、全仓清理或 `git clean -fd` 收拾现场。

## 一句话结论

天朝二期还没有到全量可交付或可制作成片的阶段，但 B1、B2 与 Incident/X 的启动 checkpoint 已解除。B1 正式 59-file 生成树 r3 在 245.770 秒 full-entry GREEN；fresh B2 r2 以 119 files / 8,891,635 B 在 164.781 秒 GREEN；Incident/X r3 又以 135 files / 9,158,442 B 在 188.303 秒通过 8 个入口门、3 条 marker、exact mount、material-error 0 与 cleanup。三者当前均只能写为 **startup/full-entry production-candidate GREEN**。fixed seed 的 no-launch preflight 已证明 fixture 还要求 Workforce 的 `zg361_we_open_portfolio_effect`；下一步必须只按用途拆分并闭合该入口所需 owners，再跑 seed-capable exact candidate 的 full-entry，GREEN 后才进入 seed/paused-native。Manager 43-effect owner 不在该闭包内，不应拉入。未改写的 58 文件单体 B1 的 1205.343 秒 RED 继续保留，不能把文件尺寸写成唯一根因；B2 与 Incident/X 均没有加载性能 RED，所以未触发追加文件边界 A/B。CK3 已退出；footage 仍为 0/8，G2 继续 paused。

## 当前工作清单

| 工作包 | 当前状态 | 下一项 | 预计交付窗口（接班人重新开始后） |
|---|---|---|---|
| 天朝二期代码/内容 | B1 59-file r3、B2 119-file r2 与 Incident/X 135-file r3 均为 startup/full-entry GREEN；Incident/X 用时 188.303 秒，8 gates / 3 markers / exact mount / material 0 / cleanup GREEN | 只闭合 Workforce `zg361_we_open_portfolio_effect` 所需用途分片与 exact full-entry，再进入 seed/paused-native | delayed-path/seed/OODA 尚未验证，不给全量 ETA |
| 两版最终宣传视频 | `footage_pending`，真实二期素材仍为 `0/8`，两份目标 MP4 均未生成 | 先取得 8 个 clean CK3 spans；随后再 fetch/pull 宣传工具主线、TTS、渲染、字幕审片、分别导出两版 | 素材齐后制作约 45–90 分钟，另需两轮人工审片；当前不能承诺日期 |
| 宣传工具 | 已满足“制作前更新”前置条件：`Z:\workspace\xar_promo_toolchain` clean，`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`（v0.2.1） | 正式 TTS/渲染前再次执行 `git fetch origin main --prune`，把 checkout SHA 写入两份 builder receipt | 工具本身已完成；等待素材 |
| G2 | **按用户要求暂缓**，不再扩展当前迭代 | 只有用户解除暂停后才恢复；恢复前先读 G2 专题和最新 schema boundary | 暂无 |
| open_kaishek | `Z:\workspace\open_kaishek` clean，`main == origin/main == 15ab978f879ed4562aacb74dacdaee702fbce54b`；本轮只做 effect 单文件 parser smoke | 真实正文 validator 的 `UNKNOWN_OPCODE` 与 IR/runtime SKIPPED 只记覆盖边界；不得写成 CK3/native readiness | 暂无 |

## 保留的未改写单文件 B1 RED

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

## 接班后的 B1 effect 诊断矩阵

接班人新增 `tools/phase2_b1_effect_bisect.py` 与回归测试，精确绑定原 B1 三文件输入，按
77 个完整顶层 effect block 生成不可覆盖、diagnostic-only projection。所有轮次使用同一
CK3 `1.19.0.6`、EXE SHA、probe SHA 与新冷 userdir，逐轮串行，自然清理。

| 候选 | 正文结构 | full-entry | report SHA |
|---|---|---:|---|
| all-stub r2 | 0 real / 77 stubs | **GREEN / 255.113 s** | `C08C84E6…43FA` |
| left-real | 0–40 real | **GREEN / 180.403 s** | `130B7B6D…D5CD` |
| right-real | 41–76 real | **GREEN / 178.968 s** | `0F4B8C00…D8BE` |
| event-root closure | 61 real / 16 stubs | **GREEN / 181.360 s** | `5DADA085…C33F` |
| closure + excluded A | 70 real / 7 stubs | **GREEN / 193.588 s** | `17382699…0538` |
| closure + excluded B | 68 real / 9 stubs | **GREEN / 184.817 s** | `7BE948D9…E1E7` |
| all-but-76 | 76 real / only #76 stub | **GREEN / 171.228 s** | `AF250EEB…F9EA` |
| balanced-files | **77/77 原始正文、0 stub；41/36 块拆两文件** | **GREEN / 180.396 s** | `CB5CB519…337F` |

八轮的主菜单、选角、开始、HUD、地图、暂停、candidate mount 与 game-state-ready 门均
为 true，三类 marker 齐全，probe `material_error_lines=[]`，cleanup 均 GREEN。权威路径、
projection/block/preflight/open_kaishek/report/screenshot/log 哈希已追加到外层
`_runtime/phase2-evidence-index-20260903.{json,md}`。

`balanced-files` 的两份 effect 为 255,134 / 240,709 B；77 个定义正文逐块与原单文件
byte-identical。它是最有价值的修复候选，但当前仍只是 disposable projection：真子集
GREEN 不能推出其 union GREEN，一次旧单文件 RED 也不足以唯一证明文件尺寸因果。
open_kaishek 只证明真实正文单文件 parser 0 诊断；validator 的 `UNKNOWN_OPCODE` 与
IR/runtime SKIPPED 是工具覆盖边界。footage、seed、native paused snapshot、observer 与
production loop 均未晋级。

## 正式 generator split 与 full-entry checkpoint

- `mod_zhongguo_style/tools/gen_361_b1_runtime.py` 已将旧正文从统一 source 渲染，再在
  block index 41 / `zg361_b1_finalize_agenda_audit_effect` 前拆为两份生成文件；定义数
  41+36=77，跨文件唯一，两份均有 UTF-8 BOM 与 generated header。
- 正式 parts 为 255,133 B / SHA `E8CA67B729E6054B3FDC56A7D66DBD00C7DD2A15EA42BBF0665E0BAF6458D486`
  和 240,700 B / SHA `1F2D76436DE74FB37698103F90ADC029BAC2AC16DD75B29E98D428E3E33F663C`；
  去掉各自 header 后重组为 495,777 B / `CDB388005FFEAC6D332380E910FBBF929F49871047E118D047C63B8751C001B4`，
  与旧 monolith 逐字节一致。generator `--check` 及 B1/scoreboard/manager/central 共 167 tests GREEN。
- 正式 projection：`_runtime/phase2-b1-formal-split-20260903-r1`，59 files / 7,858,254 B；
  source tree `DF46E56EE668265DF71C2AB05C237D52BFD602F8C9CC18C023107EC35836B2D2`，
  formal tree `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`，
  projection SHA `5E97C3D8BEECED78844BC2D868FE6B49FE5A5FBA837BBB896D367E78F94E4808`。
- r1/r2 因 probe 从独立工作树推导出不存在的游戏目录，在 0.330/0.312 秒启动前 RED；
  两轮均未启动 CK3、cleanup GREEN，report SHA 分别为 `360DC299…6BF9C` / `C68D9F8B…A4B73`。
  它们是保留的 harness 配置失败，不计作候选内容结果。
- r3 显式绑定 exact EXE 后在 **245.770 s full-entry GREEN**。report
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b1-formal-split-full-entry-20260903-r3\report.json`
  SHA `22C7ECA8D071812381FC753DF8E6E29CEFB435C6ACFE0EE3D42D3647A1DA3980`；
  8 个 gate 全 true，三条 marker 齐全，material-error 0，地图 SHA
  `5741C388D6A825A75C5B448482DA76047DB659CCDDAAF851BE0C0D28135C6A3F`，
  cleanup `ck3_running_after=false`、userdir retained。
- 诚实边界：此 GREEN 只解除正式 B1 startup/full-entry checkpoint；还没有执行 B1 delayed-path、
  seed、native paused snapshot、observer 或 production OODA，也没有产生任何 footage。

## 已完成的可复核批次与耗时

| 批次 | 规模 | 实机结果 | 耗时 | 证据 |
|---|---:|---|---:|---|
| 53-file pure case-kernel（旧 lineage） | 53 files / 7,313,274 B | **GREEN**：主菜单、选人、开始、HUD、地图、暂停及三条 game-state marker | 300.656 s（约 5:00.656） | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-minimal-full-entry-20260903-r3\report.json`，SHA `AF6F671FFAB9CC38F96EA9446A276D81362274B75E813C403F3BEA51185BA883`；tree `BDB8D89162C1C4B01058A3987FE916BD0DDA16CBD67EDABB412ED9E3F0FD7265`；地图图 SHA `FCE77CF853CD68FBA4461A84000694CBCE66FEA4DB73EA3D552A706D41818F3B` |
| 55-file safe-core ABI | 55 files / 7,325,646 B | **GREEN**：同一完整进图门槛，cleanup GREEN | 688.087 s（约 11:28.087） | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-next-increment-safe-core-full-entry-20260903\report.json`，SHA `00DB2B83503F6AE66216925897E4394C5AFC32300602DFA9ED6A46700BD3D422`；tree/formal `3D96D527D0486944492010DB05DDC4EB50C7BB3777DFCCDE4509CDE4E48659B7`（以 report/projection 为准）；地图图 SHA `91F61D2107B6B06BD4B8224A73F4F2D02FAA59FB03E8A03C0819A61456D2E4BE` |
| 58-file B1 closed-ZH（本轮） | 58 files / 7,858,198 B | **RED**：20 分钟仍停启动页，未到主菜单 | 1205.343 s | 上一节 report/screenshot/debug/error；这是当前失败 attempt，必须保留 |
| 59-file B1 balanced-files（接班诊断） | 59 files / 7,858,264 B | **GREEN**：全部 77 个原始正文、0 stub，双文件结构完整进图 | 180.396 s | report `CB5CB519B05B865720CA7F3BD8FA6B984690FE0B2D6DAF6DB8E3FC1C2BDA337F`；tree `AB0049EA3A53C0CD53AD6290AE8F8DA0A876FB281A2EAD04A272F145C22F14BC`；地图 `F0FB03D13AB6DEEC31A7324FD87F8D3E1E7BF12C403BB74A4215A321DFD3D2EC` |
| 59-file B1 正式 generator split r3 | 59 files / 7,858,254 B | **GREEN**：正式两份生成文件完整进图，8 gate、3 marker、material 0、cleanup GREEN | 245.770 s | report `22C7ECA8D071812381FC753DF8E6E29CEFB435C6ACFE0EE3D42D3647A1DA3980`；tree `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`；地图 `5741C388D6A825A75C5B448482DA76047DB659CCDDAAF851BE0C0D28135C6A3F` |

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
9. **真子集 GREEN 不是 union GREEN。** 左右半区、互补 excluded 组和 76/77 候选均能进图，只能排除它们各自“单独充分触发”；不得用集合单调性把原单文件 B1 改写为 GREEN。全正文双文件 GREEN 支持结构修复，但根因仍需正式生成树复验。

## 下一轮操作建议

1. 先读 [`docs/phase2-promo/phase2-incremental-startup-batch-plan-2026-09-03.md`](../phase2-promo/phase2-incremental-startup-batch-plan-2026-09-03.md)、[`docs/phase2-promo/README.md`](../phase2-promo/README.md) 和 [`phase2-safe-core-next-domain-closure-2026-09-03.md`](../phase2-promo/phase2-safe-core-next-domain-closure-2026-09-03.md)。确认没有 CK3 后再做静态检查；不要重跑已证明的 53/55 基线或七个 stub 子集。
2. balanced-files 的 41/36 边界已下沉到 `tools/gen_361_b1_runtime.py`，正式 r3 已 full-entry GREEN；不要再重跑旧单文件或七个 stub 子集，也不要手改 `GENERATED FILE` 产品。
3. CK3 槽位严格串行：固定 `1.19.0.6` EXE、已验证 profile/cache 和 probe 脚本；一次只跑一个候选，timeout 先用 1200 s。每 30–60 s 只读记录进程、debug.log、memory 和 marker；若自然结束，保存 report/screenshot/log hash，确认 `ck3_running_after=false` 后再开下一轮。
4. exact `_runtime/phase2-b2-production-closure-20260904-r2/product`（119 files / 8,891,635 B）已通过 full-entry；随后 no-launch
   seed preflight 证明 fixed fixture 还要求 Incident `zg361_ip_open_x_case_effect` 与 Workforce
   `zg361_we_open_portfolio_effect`，所以不能直接复用 B2 r2 进入 seed。full-entry GREEN 不替代 delayed-path 或生产功能验收。
5. Incident/X 已由下面记录的 r3 exact candidate 完成静态闭包与 full-entry，关闭第一个 fixture root；旧 Manager 简中候选
   不在 fixed seed 的当前闭包内。下一步必须只按用途拆分 `zg361_we_open_portfolio_effect` 所需 Workforce owners 并完成 exact
   full-entry，之后才启动 seed/paused-native。
6. 项目所有者在 2026-09-04 明确要求：进入 B2 前先按用途/调用链拆分 effect，目标每文件 `1–10` 个，原则上不超过 `20` 个；超过 `20` 必须记录理由和实机证据。若后续出现没有明确 material/parser 首错的加载性能 RED，优先按 `docs/testing-workflow.md` 做同条件文件边界 A/B，并把结论限制为“文件边界/单文件体量很可能参与”。
   B2 自身现已完成 25 个用途分片：152/152 unique、每片 `1–9`、清单 SHA `06274A5E…7FAB`，静态/投影/release GREEN；该分片
   工作包独立交付时尚无 CK3 live，后续组合 r2 live 见下文。正式提交 `e1297f83738fd61d53812406b26e23637201d2c5` 已推送。其 Workforce effect owner 现也已拆为 76 个用途片：
   324/324 parity、每片 `1–10`、无超限例外；B2 40-effect 闭包精确落在 16 个完整片内。Workforce event owner 也已从
   `168,729 B / 149-event` 单体拆为 35 个用途片：每片 `1–7`，B2 19-event 闭包精确落在 7 个完整片内，manifest SHA
   `1E1EEE66…F8DA`；generator `--check`、主测试 116/116、全量生成/业务、visual/projection、release 与
   `validate_local.py` 均 GREEN，413-file release manifest/ZIP 为 `E68E89F3…60B4` / `4A7C7995…1E67`。
   上述分片工作包独立交付时 CK3 live 待完成；下述组合 r2 已关闭 full-entry 门。
   fresh r2 由冻结 B1 的 59 文件加 60 个 overlay 文件组成；B2 为 25 个 effect 分片 / 152 effects（每片 `1–9`），其中 Workforce
   依赖精确选择 16 片 / 40 effects 与 7 片 / 19 events。三 root 固定点为 71 effects / 28 events，全部 selected events 为 51；
   无 legacy monolith、stub、duplicate、missing callable 或 missing event。B2 起新增的 60-file overlay 含 44 个 effect 文件 / 218
   definitions，最大为 probation owner 的 15，且只有它超过 10；overlay 中超过 20 为 0。119-file 整树继承冻结 B1 的 5 个
   grandfathered 超 20 effect 文件：B1 part1=41、part2=36、case_kernel=229、`zg361_effects`=26、
   `generated_mechanism`=1449；它们不是本轮新增，并已有 B1 full-entry 证据。source/formal/file-list SHA 分别为
   `F3B36DFDBE74827FF373B06C7C621D1EC72AA15E575F5ABBF1186E636C625184` /
   `3DD3DA79F11EC892DF72024E25EE985ACAB26E21FD4C1281C35E5DEB0642C4D3` /
   `6C3FE72E3FBB3E1AB6543BEE9226F24203D1063951999AAF6BD7E9053B7533FF`；projection SHA
   `2C8F0979113F75866191C3AE10C699F3801D83AEF91ADCFD9C4B526B469EAE28`，contract SHA
   `F5BC105C1C3EF8E55E82053F61D3B453E6B92A7E0AE224EDECBD072B6EF49180`。r1 只保留为已被 r2 取代的静态 artifact。
   exact r2 live artifact 为 `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-no-stub-full-entry-20260904-r1`；164.781 秒
   full-entry GREEN，8 gates、3 markers、exact mount、material errors 0、`cleanup.ck3_running_after=false`。`report.json` SHA
   `4DAAD3649E4FC37373EF2B95F9DE24FB15D23E1319403F37A89228E4B44674F1`，`complete_entry_map.png` SHA
   `F867A24AE1267BA032BC8CDB2EE623A966FF8E7ED1AE9ED78251B115958F875C`。没有加载性能 RED，故未做 A/B。
7. 视频路线保持两条独立交付：人物版与制度群像版都不能因另一版完成而自动签核。只有 8/8 clean CK3 spans、source review、字幕/媒体检查和 builder receipt 齐全后，才运行 TTS/render/export；制作前再次 fetch 宣传工具 `origin/main`。
8. G2 维持暂停。open_kaishek 的 15ab978 是明确的 activity-schema negative boundary；它的 RED 是覆盖缺口，不是 CK3 runtime 失败。恢复时先重跑 Maven/fixture 并更新本项目绑定，不要猜 activity opcode allow-list。

## Incident/X r3 用途分片与实机 checkpoint

- Incident 旧 aggregate effect 为 `700,085 B / 124 effects`，旧 aggregate event 为 `8,573 B / 54 events`。generator 现按
  capture/probe/KPI、X/Y/Z apply/debt/dispatch/deadline/lifecycle 与 portfolio 用途输出 27 个 effect 分片和 12 个 event
  分片；所有分片最多 7 个定义，没有超过 10/20 的例外。124/124 effects 与 54/54 events 的顶层 block 保持逐字节 parity，
  历史 aggregate SHA-256 为
  `0C228FAABB5F6B7DCDABFD32A071CA82F0C1EF15C08AB0BD07C25AF3A467DACD` /
  `49577D5475FBF6B22006021F4FADED2A248C7E193840A283FB043F7AAAC0E091`。
- X production 增量精确选择 11 个 effect 分片 / 47 个 Incident effects 与 4 个 event 分片 / 20 events；连同冻结
  case-kernel 后固定点为 `60 effects / 20 events / 6 triggers`，没有 Y/Z 定义夹带。16-file overlay 为 266,807 B。
- exact 候选位于 `_runtime/phase2-incident-x-production-closure-20260904-r3`，共 135 files / 9,158,442 B；
  source/formal/file-list SHA-256 为
  `ACC693206AAA03AEEDFB829911778275ED4D4F2EEF31CF4DCE6DE7D46F34BF3E` /
  `AF8F0DECE9477FDD60B6C96D0E09A27BFC9E55CEED40A9804B70ACB986D57A2D` /
  `045F56D78FB036CDF69225912F9B046673FCD528E99A69571363133A65EA2262`；projection/contract SHA-256 为
  `CF379F38DA8C471DDCCDB6522D7E0864098596737862B5E2A703AECA94E40CB7` /
  `ED4B5E82430187B1C79E2AEFE29748C5D51749782CC340644DB434C14A0B468A`。
- 首次 live attempt r1 在 `0.338 s` 因默认 worktree 游戏路径不存在而 harness RED；CK3 未启动，report SHA-256
  `1CF7A2B014D8BBD9F39C6D1423B2E39BB5B7BCDBA21D1505CD4CECB7F5DFDC51`。r2 显式设置 `XAR_CK3_EXE` /
  `XAR_CK3_GAME_DIR` 后，在 exact CK3 `1.19.0.6`、EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 上以 188.303 秒完成 full-entry GREEN：
  8/8 gates、3/3 markers、exact mount、material errors 0、`cleanup.ck3_running_after=false`。artifact 为
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-incident-x-full-entry-20260904-r2`；report/map SHA-256 为
  `1D41298B8987AA473304AE70FC53628639DE7700BBE5A9D7484A6BF76F566FE2` /
  `F75097D9C20B610F81CA60837DF879865E26866F65AC76E7D40C1DF300C34B2A`。没有加载性能 RED，故未做追加 A/B。
- 用途分片与闭包实现提交 `df77ed636c51c51f99f534d8efbb559b94c639d2` 已推送。Incident/X 当前只能写为
  `startup/full-entry production-candidate GREEN`；X delayed-path、KPI consumer、paused native 与 seed 仍未验收。
- fixed seed 五个 roots 的固定点为 `385 effects / 161 events / 6 triggers`；相对 Incident/X r3 还需 Workforce
  `307 effects / 140 events`，6 triggers 已有，并补 3 个文件中的 24 个可见 loc keys（AD 15、attribution 5、
  remediation 4）。Manager 43-effect owner 不在闭包内，不应顺手纳入。

## 交接时的授权边界

- 可以在 CK3/Paradox 弹出协议或通知时按用户既有授权同意/关闭；右下角 Toast 可清理。
- **禁止**任何购买、付款、充值、商店下单或其他付费动作；看到购买/付款/商店语义立即停在安全按钮前。
- 不要把点击协议、启动成功或一场 fixture 当成 Phase2 完成；不要自动发布未审片视频。

## 现场核对清单

- [x] 当前 B1 round 自然结束，report/screenshot/log 已保存。
- [x] `ck3.exe` 与测试 python 进程均已退出；没有留下运行中的 CK3。
- [x] 9 月 3 日日报已正式收口；SHA `6A56353FA7A6E15AB4B0EF6C0E816760A417EF03EC4C21CFC1908740D439B66A`。9 月 4 日日报与早会已创建。
- [x] Phase2 evidence index 已收录诊断矩阵与正式 r3；JSON SHA `CE11D266E6808E582BEC5B3659E0359CCE71204D9545F08C5A1A041C13A7F580`，MD SHA `892CACBA91A6C88453AD2CEC587AA82D7F5971D2CCEADD6C63055420FE4FE7BA`。
- [x] 宣传工具 checkout 已更新并与远端主线一致；没有启动 TTS/render，也没有生成占位 MP4。
- [x] G2 已按用户要求暂缓；open_kaishek 工作树 clean。
- [x] B1 正式拆分与证据主提交 `4aea7afe3f6d3f4f82f7551869aba8faeae0c66b`；非强推 merge
  `89808bb5799d651847b14460e38c4369e94209f7` 已推送，分支与远端同步。
- [x] B2 正式用途分片提交 `e1297f83738fd61d53812406b26e23637201d2c5` 已推送；25 片均为 `1–9` effect，当前没有超限例外。
- [x] Workforce effect 的 76 片实现与静态证据已由 `76fbf436a023f7d022f3eab6581e43fc632be3d0` 提交并推送；后续已纳入 exact r2 full-entry。
- [x] Workforce event 已实现 35 个用途片，149/149 unique、每片 1–7，B2 19 events=7 片精确并集；静态/release 矩阵 GREEN；
  提交 `0865589cb7ef37160e50247f0fdeb1f27a03fe54` 已推送；后续已纳入 exact r2 full-entry。
- [x] fresh r2 无 stub B2 closure 已以 119 files / 8,891,635 B 在 164.781 秒通过 exact full-entry；report、地图截图与 cleanup 证据已保存。no-launch preflight 随后证明它不能单独满足 fixed seed fixture。
- [x] Incident 已拆为 27 effect + 12 event 用途分片，每片最多 7；exact X r3 候选以 135 files / 9,158,442 B 在 188.303 秒通过 full-entry。实现提交 `df77ed636c51c51f99f534d8efbb559b94c639d2` 已推送，r1 harness RED 与 r2 GREEN artifact 均保留。
- [ ] seed 前仍须闭合 Workforce `zg361_we_open_portfolio_effect` 所需 owners 的按用途分片、exact closure 与同树 full-entry。
- [ ] 下一位接班人重新开始前，先确认工作区 dirty/untracked 清单，不要覆盖或清理上述 disposable artifact。

这就是当前可以安全交出的边界：正式 B1、fresh B2 r2 与 Incident/X r3 的 startup/full-entry checkpoint 均已 GREEN，失败、修复与 cleanup 证据齐全；但 Workforce seed 入口闭包、delayed-path、seed、native/production loop、8/8 素材与两部最终宣传视频仍未完成。
