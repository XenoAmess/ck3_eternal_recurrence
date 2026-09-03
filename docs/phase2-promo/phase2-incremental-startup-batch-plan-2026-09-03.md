# 天朝二期分批启动验证计划（2026-09-03）

## 先说结论

“批次”有两个口径，不能混为一个数字：

1. **产品清单口径：13 个累计阶段**。其中第 0 阶段是已经验证过的天朝一期兼容基线（51 个文件），之后追加 12 个功能簇，最后到 279 个文件的二期全量投影。
2. **实际 CK3 诊断口径：17 个固定 checkpoint**。为使每次结果可归因，需把跨域依赖拆开（case kernel、safe core、B1、B2、central integration、scoreboard 等），因此不能把上面的 13 个名字直接当成 13 次可独立启动的闭包。

第 7 个 checkpoint（workforce）另设条件性递归二分：按首个失败边界，预计增加 **3–6 次** 单槽启动。因此本轮实际预计为 **20–23 次 CK3 启动**；若 workforce 整体一次通过，则为 17 次。这个范围是诊断计划，不是把尚未发生的结果预报成已完成。

## 17 个固定 checkpoint

| 编号 | 投影内容 | 目的 |
|---:|---|---|
| 0 | old-core 51 文件（一期兼容基线） | 控制组：Frontend、history、exit 0、cleanup |
| 1 | 纯 case-kernel | 验证共享 case ABI 本身 |
| 2 | safe core ABI（不含整合型 dispatcher） | 给后续域提供最小基础，避免把缺失符号同时引入 |
| 3 | B2 | 单独验证 result/notice 消费链；必要时只加明确标记的 stub |
| 4 | B1 | 单独验证 cycle/KPI 链 |
| 5 | incident | 验证 X-case 与 incident KPI |
| 6 | manager | 验证治理链，并提前闭合 workforce 的 M360 owner |
| 7 | workforce closure | 先验证 central m275 adapter，再加入完整 workforce 文件 |
| 8 | phase3 | 验证后续指标域 |
| 9 | career | 为 feedback 提供 HC owner |
| 10 | feedback | 验证 promotion/PIP |
| 11 | credit | 独立验证 credit 项目 |
| 12 | compensation | 独立验证 compensation/generated |
| 13 | real central integration | 所有 owner 齐全后替换临时 adapter |
| 14 | late current-core integration | 最后并入完整 effects/events/mandate/interactions |
| 15 | scoreboard 三件套 | 三个 scoreboard blob 一起验证；单独记录其体量风险 |
| 16 | exact 279-file endpoint | 复核最终累计树、完整投影与清理 |

## B2 起 effect 文件布局

从 checkpoint 3 / B2 起，effect 文件必须按用途与调用链分组，目标每文件 `1–10` 个顶层 effect，原则上不超过 `20` 个。
生成内容必须在 generator 层拆分，并由静态测试逐文件检查定义数、跨文件唯一性及 `--check` 覆盖；投影与发布清单必须枚举全部分片。
确需超过 `20` 个时，须在本计划或对应专题记录用途、定义数、字节数、不能继续拆分的理由及测试/实机证据。

若某轮出现没有明确 material/parser 首错的加载性能 RED，先按
[`testing-workflow.md`](../testing-workflow.md#加载性能-red先验证文件边界与单文件体量) 的文件边界 A/B 规程尝试继续拆分。
B1 已验证的 `41 + 36` 结构是恢复期冻结基线，不作为 B2 及后续文件布局模板。

## 条件性 workforce 二分

workforce 有 324 个顶层 block、约 4.64 MB；静态扫描还发现跨域 callable 和高入度 generated mechanism helper。若 checkpoint 7 失败，不截断 block、不修改生产文件，而是在同一个 old-core + 已闭合依赖基线上按完整 block 边界递归二分，最多保留 3–6 个诊断轮次。每轮都要记录新增文件清单、树 SHA、首个日志 marker 和内存曲线。

## 每轮硬门

- 离线 Gate A：累计 product 的文件数、字节数、tree SHA 与 materializer 报告完全一致；projection 名称和 manifest SHA 一致。
- 离线 Gate B：从 known-good profile 复制全新 disposable userdir；settings SHA、shadercache 数量/字节/tree SHA 一致；不得复用已启动目录。
- CK3 只能单槽串行。完整 GREEN 至少要看到窗口、`Frontend`、`End loading of history`、200 heartbeat、exit 0 和 cleanup；`Frontend` 与 history 到达即可记为 `STARTUP_GREEN`，未收到 heartbeat 只标为 observer RED，不倒推 CK3 启动失败；若 `error.log` 有 parser/projection symbols，再叠加 `PARSER/PROJECTION_RED`。
- 任何目标/源码快照不配套（例如旧冻结 runner 不支持命名 projection，或 autoplayer 缺少 runner 所需常量）都记为 `INVALID_TARGET/PREFLIGHT_RED`，不计作 CK3 失败，也不启动错误目标。
- 失败 attempt、日志、report 和 SHA 保留，不被后续 GREEN 覆盖。

## 当前状态

- 历史 coarse 工具曾生成 13 个累计 product tree，最终 broad 目标为 279 files / 29,351,046 B；但其逐批 Gate A 实际只核对 count/bytes（仅末批绑定 tree SHA），Gate B 只核对 immutable profile reference、没有核对实际 disposable userdir。因此旧“0–12 A/B 全 GREEN”声明已撤回，该 inventory 只保留为历史分组草案，不能充当 hard gate 或 live 证据。
- 历史 old-core、部分 core/case-kernel 组合有 Frontend/clean-exit 证据；30 分钟 monolith control、workforce monolith 和 B7 stub 仍停在 `Total of : 881`，尚未形成完整 history 证据。c91 的 batch01 `core-current` 则已于 15:04:20 到达 `Frontend` 与 `End loading of history`。
- 历史名义批次 1（`core-current`）的 c91 实测已实际启动 CK3：启动层为 `STARTUP_GREEN`，但整体 report 仍为 RED，decision 仅为 observer coverage 的 `heartbeat_not_observed`；`error.log` 有 176 行 projection-missing symbols（含 `Unknown effect`/trigger 等），故分类为 `STARTUP_GREEN / PARSER-或-PROJECTION_RED`，不是 CK3 启动失败。报告为 `Z:\\ck3_mod_rewrite\\_runtime\\formal-phase2-incremental-01-core-current-c91-20260903\\artifacts\\runner-report.json`，SHA-256 `1371E0C601253C555EF46DB5315779017D9BA278957C7BA88ED69D6726EA423B`。它不是修订主线的 P1 `pure-case-kernel`；后者及 P2/P3/P4/P6 的实测状态见下表。旧 `4ff` preflight RED 仍为 `ck3_launch_attempted=false` 的启动前源码配套问题，不计作 CK3 失败。
- 用户取消了 7200 秒续测；后续沿用原有短诊断窗口，首失败即保存证据并进入窄二分，不再无条件等待两小时。

### 2026-09-03 实测增量（滚动更新）

| checkpoint | 当前结论 | 首要证据/阻点 |
|---|---|---|
| P1 `pure-case-kernel` | `STARTUP_GREEN / PARSER-PROJECTION_RED` | 51-file 一期基线加 2 个 case-kernel 文件到达 `Frontend` 与 history；缺后续域符号属于刻意投影截断 |
| P2 `b2-closure` | `STARTUP_GREEN / PARSER-PROJECTION_RED` | 64 文件到达 `Frontend` 与 `End loading of history`；首错为 B2→workforce 跨域 owner 缺失 |
| P3 `b1+b2-closure` | `STARTUP_GREEN / PARSER-PROJECTION_RED` | 77 文件到达 history；仍由同一 workforce/incident 后续引用阻断，未见原生早期崩溃 |
| P4 `callable-core` | `LOAD_BOUNDARY_RED` | 66 文件在 `Total of : 881` 停滞；首错为缺 `zg361_p2c_schedule_m275_runner_requisition_effect` 与一处 appointment 语法 |
| P4-m275 disposable stub | `LOAD_BOUNDARY_RED` | no-op shim 清除 parser error，但仍停在 881；证明 m275 缺口不是唯一停滞原因（stub 不进生产） |
| P6 `central-callable` | `PARSER-PROJECTION_RED` | m275 owner 已纳入；首错收敛到 6 个 portfolio owner、旧 trigger 替换和 `revoke_court_position` block，下一轮做最小 disposable closure |
| P6a `portfolio/B1/revoke closure` | `LOAD_BOUNDARY_RED` | 74 文件 / 20,538,639 B；静态与 `error.log` 已清零，但 `Total of : 881` 后未见 history；这是 P6 的条件修复分支，不新增固定 checkpoint |
| P6b `workforce four-block stub` | `LOAD_BOUNDARY_RED` | 74 文件 / 18,936,168 B；保留 324 个顶层符号，仅置空 m360 materialize/route 四块，仍为 `Total881`、无 history |
| P6c `materialize-only` / `route-only` | `LOAD_BOUNDARY_RED` | 两个互补投影（分别 19,590,855 B / 19,883,952 B）均 `error.log=0`、`Total881`；排除这两组作为唯一根因 |
| P7 `portfolio-event closure` | `PARSER/PROJECTION_RED` | 99 文件 / 20,929,655 B；发现 323 条 missing-loc（311 个唯一键），仍停在 881 |
| P7a `event localization closure` | `LOAD_BOUNDARY_RED` | 补齐 117 个 loc 文件后 216 文件 / 21,360,068 B，311/311 键覆盖、`error.log=0`，仍停在 881；说明 loc 缺口不是 native loader 根因 |
| 265-file `workforce A+B` physical split | `LOAD_BOUNDARY_RED` | 将 4.64 MB monolith 无损拆为 part A/B，内容重组 SHA 一致；265 文件 / 15,938,098 B，仍 `error.log=0`、`Total881`，物理拆文件本身无效 |

### P7 微批次（按用户建议进一步缩小）

P7 原始 event closure 为 **99 文件 / 20,929,655 B（约 19.96 MiB）**；补齐本地化后的 P7a 为 **216 文件 / 21,360,068 B（约 20.37 MiB）**，确实不适合直接作为第一轮归因实验。现改用已经到达 `Frontend` 与 `End loading of history` 的 P3 `03-b1-b2-closure` 作为母版（77 文件 / 8,234,687 B），只追加 5 个 workforce 事件注册文件：

1. `events/zg361_workforce_exit_fact_events.txt`（1,920 B）
2. `events/zg361_workforce_normal_exit_fact_events.txt`（3,312 B）
3. `events/zg361_workforce_probation_fact_events.txt`（1,286 B）
4. `events/zg361_workforce_remediation_fact_events.txt`（2,427 B）
5. `events/zg361_workforce_rehire_fact_events.txt`（950 B）

该微批次只增加 **9,895 B**，挂载树为 82 文件 / 8,244,582 B（约 7.86 MiB）。它刻意不带对应 scripted effects 或本地化，实验问题限定为“事件文件注册本身是否改变 loader 边界”；若能保持 history，再逐项追加 callable/effect 闭包。若出现 parser/projection 错误，按日志首个符号继续一文件递归，不把失败归因于整个 P7。该投影为 disposable，不能当作正式发布树。

上述 `STARTUP_GREEN` 只表示 CK3 启动层越过窗口/history；只要仍有 parser/projection 错误，就不算该功能簇完成。P6a–P7a、互补 stub 与 265-file A+B 都是条件诊断分支，不计入 17 个固定编号。当前修订 checkpoint 索引实际只物化到 00–07；08–16 仍是待执行计划，不能写成已运行或通过。每轮 report、日志和 SHA 独立保存，后续不会覆盖失败证据。

### B1 effect 条件二分与拆文件候选（最新）

| 诊断候选 | 当前结论 | 耗时 |
|---|---|---:|
| all-stub | `FULL_ENTRY_GREEN` | 255.113 s |
| left-real | `FULL_ENTRY_GREEN` | 180.403 s |
| right-real | `FULL_ENTRY_GREEN` | 178.968 s |
| event-root closure | `FULL_ENTRY_GREEN` | 181.360 s |
| closure + excluded-A | `FULL_ENTRY_GREEN` | 193.588 s |
| closure + excluded-B | `FULL_ENTRY_GREEN` | 184.817 s |
| all-but-76（76/77 真 block） | `FULL_ENTRY_GREEN` | 171.228 s |
| balanced-files（77/77 真定义、无 stub） | `FULL_ENTRY_GREEN` | 180.396 s |

`balanced-files` 只改变文件布局：全部 77 个定义的正文与原始 effect 逐 block 字节一致，拆成 255,134 B 与 240,709 B 两个 effect 文件；投影总计 59 files / 7,858,264 B。该结果把拆文件提升为可实施候选，但这些条件分支不计入 17 个固定 checkpoint，也不自动通过 checkpoint 4。未改写的 58-file 单 effect full B1 仍只有一次 1205.343 秒 RED；所有真子集与拆分候选 GREEN 不等于原始 full-union GREEN，不能宣称根因已经唯一证明。

下一步仅需将 balanced-files 方案重建为可审阅候选，验证正式 B1 业务与全量 projection 门；通过后才进入 seed。open_kaishek 对这些投影只做单 effect 离线 parser smoke，含真实正文的 validator 仍为 `UNKNOWN_OPCODE`、IR/runtime `SKIPPED`，不得用来替代 CK3 实机结论。footage 保持 `0/8`，两条 MP4 未生成；G2 按用户要求暂停。

### 正式 generator split 与 checkpoint 晋级

上述 disposable 结论现已由正式生成器候选承接：生成结果为 **59 files / 7,858,254 B**，两个 B1 effect 文件包含 `41 + 36` 个定义；77 个定义按原顺序重组后的正文与原始单文件 **exact**。formal tree SHA-256 为 `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`。

| attempt | 结果 | 解释边界 |
|---|---|---|
| r1 | 约 0.3 s game-path config RED；CK3 未启动 | probe 配置失败，不计内容/live |
| r2 | 约 0.3 s game-path config RED；CK3 未启动 | probe 配置失败，不计内容/live |
| r3 | `FULL_ENTRY_GREEN`，245.770 s | 8/8 gates、3 markers、material 0、cleanup GREEN |

因此固定 checkpoint 4 可以晋级为 **startup/full-entry production-candidate GREEN**；此前“balanced-files 条件分支不自动通过 checkpoint 4”的历史判断由本节正式 r3 结果推进。它仍不是 delayed-path、seed、生产 OODA 或完整 Phase2 GREEN。原始未拆分单文件 full B1 的唯一 1205.343 秒 RED 继续作为失败 attempt 保留；正式拆分提供可实施候选，但不唯一证明根因。

### 2026-09-04 B2 正式用途分片

旧 B2 单体 `253,920 B / 152 effects / 70B38FA3…3C4F2` 已从 canonical 产品树移除；generator 现按机制用途输出
25 个 effect 文件，精确覆盖 152/152 个唯一顶层定义，每片 `1–9` 个、合计 `250,551 B`，没有超过 `10` 或 `20` 的例外。
逐 block 正文与历史内存渲染字节一致，分片清单 SHA-256 为
`06274A5E0D89EF97C19EF3C099E8AEF946C4153BC78C065EC260806D27F67FAB`。完整映射见
[`361-b2-runtime-spec.md`](../../mod_zhongguo_style/docs/361-b2-runtime-spec.md)。

静态结果：B2/manager 聚焦 142/142、CI 同口径 `test_gen_361*` 107/107、`test_zg361*` 1256/1256、
`validate_local.py`、native normal-exit source-contract 1/1、projection 8/8、release tests 7/7 与可复现 release `--check` 均
GREEN；新 release 为 304 files，manifest `DF1741C3…02D0`、ZIP `2C18050A…1884`，broad/release 均只有 25 个分片、没有旧单体。
这些只把 B2 文件布局提升为 **static-ready**，没有新增 CK3 live 结果。

B2 的三个直接 Workforce owner 沿 effect 调用、literal event ID 与 `EVENT = <id>` 参数化 deadline ABI 的真实静态可达链会进入
71 个 effect / 28 个 event。旧 `68 / 24` 扫描漏掉了 `zg361we.4606/.4706/.4801/.4901` 四个参数化事件，以及由此新增的
三个 effect；该旧口径现已被取代。其中
旧 `zg361_workforce_endgame_runtime_effects.txt`（`4,636,271 B / 324 effects`）现已由 generator 替换为 76 个用途分片：
324/324 顶层 block 按历史顺序逐字节一致，每片 `1–10` 个、无超过 20 的例外，总计 `4,635,596 B`，清单 SHA-256 为
`E5DD22CEF71D60E069884A27BE924234B4FAD42490AEF2B52B966AFD95585858`。B2 的 40 个 Workforce effect 正好由其中 16 个完整分片
承载（341,602 B，extra=0、missing=0）；该布局目前只到 **static-ready**，没有新 CK3 live。

旧 `zg361_workforce_endgame_runtime_events.txt` 的冻结基线为 `168,729 B / 149 unique events`，SHA-256
`637F65CC72C176E6E19BE982F41B203DC326047939B79A80E5E43D3A9D361EF7`。generator 现将其替换为 35 个用途分片：
149/149 unique、合计 `175,403 B`，单片 `1–7` 个 event（最小 `349 B`、最大 `16,842 B`），没有超过 20 的例外；
数量分布为 `{1:2, 2:7, 3:5, 4:4, 5:4, 6:9, 7:4}`，manifest SHA-256 为
`1E1EEE665105139653BC3D00B092522A41C97FE16164E27ACBDB6FC0C967F8DA`。B2 所需 19 个 Workforce event 恰好由 7 个完整分片
精确承载，extra=0、missing=0，不再因旧单体对约 210 个 effect 的静态引用拉回几乎全图。generator `--check` 覆盖 120 个输出，
Workforce 主测试 116/116、`test_zg361*` 1265/1265、`test_gen_361*` 107/107、visual/projection 8/8、release 9/9 与
`validate_local.py` 均 GREEN。可复现 release `--check` 为 413 files，manifest `E68E89F3…60B4`、ZIP `4A7C7995…1E67`；
这些仍只记 **static-ready / no new CK3 live**。

下一步物化 119-file、无 stub 的 B2 production closure；先在同一冻结 B1 基线上跑下一 distinct
full-entry，GREEN 后才复用完全相同的 projection/hash 进入 seed。不能把旧 stub checkpoint 冒充生产 B2。
footage 仍为 `0/8`，两条 MP4 未生成；G2 保持 paused。

## 预计时间

离线物化/预检通常数分钟。实测 full-entry 已在约 171–1205 秒间明显波动；下一 distinct 候选使用 1200 秒初始观察窗，
以阶段 marker、引擎时间和 probe wall time为准，不再沿用早期 2–5 分钟线性估算。出现无明确 material/parser 首错的加载性能 RED 时，
保留原 attempt 后立即按用途/完整顶层定义边界继续拆分并做同条件 A/B。

本计划只负责定位二期加载边界；seed、8 段 clean footage、两版宣传片仍须在闭包通过后另行验收。宣传工具在开始视频制作前必须再次确认 `origin/main` 最新版本。
