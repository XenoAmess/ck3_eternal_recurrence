# 天朝二期验收用例索引

状态：**滚动维护；下文 T0 `50%`、canonical stage `8/11`、source `3/4` 是历史快照；现行 P1 按九项机器门签收，P2 `LOCKED`**。

本文把分散在生成器测试、静态合同、CK3 runner、source registry 和宣传制作
文档中的用例统一编址。它是执行索引，不替代各专题的字段级权威定义。

## 权威入口

- 361 项批次范围、领域映射与批量验收原则：
  [`mod_zhongguo_style/docs/361-phase2-full-implementation-program.md`](../../mod_zhongguo_style/docs/361-phase2-full-implementation-program.md)
- 361 项机器可读清单：
  [`mod_zhongguo_style/docs/361-mechanism-manifest.json`](../../mod_zhongguo_style/docs/361-mechanism-manifest.json)
- 自动验收、日志、现场恢复与 GREEN/RED 规则：
  [`docs/testing-workflow.md`](../testing-workflow.md)
- 当前 promotion 长链实机取证：
  [`b1-r66-manager-subject-fix-2026-09-05.md`](b1-r66-manager-subject-fix-2026-09-05.md)
- 当前 projects/metrics provider 实机闭环：
  [`r300-r303-credit-project-resume-projects-metrics-live-2026-09-08.md`](r300-r303-credit-project-resume-projects-metrics-live-2026-09-08.md)
- 四类 registry 与八段素材边界：
  [`final-promo-non-ck3-prep-audit-2026-09-04.md`](final-promo-non-ck3-prep-audit-2026-09-04.md)
- R326 incidents/operations 第三项 source checkpoint 与 schema-v3 三源前缀：
  [`2026-09-08 日报的 R314–R326 证据`](../autonomous-agent-progress/daily/2026-09-08.md#r314r326-incidentsoperations-source-checkpoint-34)

## 状态口径

| 状态 | 含义 |
|---|---|
| `STATIC_GREEN` | 生成器、parser、schema、fixture 或纯 Python 合同通过；不代表 CK3 实机 |
| `LOADER_GREEN` | exact build 已真实加载指定 production projection，error scan 与挂载检查通过 |
| `LIVE_PARTIAL` | 真实 CK3 路径已覆盖其中一段，但目标业务后置条件尚未全部出现 |
| `LIVE_GREEN` | 同一真实 lineage 的输入、动作、独立后置查询和清理全部通过 |
| `NOT_RUN` | 可执行入口存在但本轮尚未运行 |
| `BLOCKED` | 已保存 RED artifact；必须先修复该实际阻点 |

通过数量不能换算为代码行覆盖率；项目当前没有 coverage.py/分支覆盖率报告。

## T0-P1 九项现行机器门（2026-09-10 owner revision）

`tools/run_zhongguo_acceptance.py --phase2-live-batch` 默认只执行 critical-path 路由：绑定当前 paused
candidate 的 loaded-feature manifest 与 seed，再消费 `--phase2-p1-evidence-manifest` 指定的真实证据包。只有以下九项能决定 P1：

| # | P1 硬项 | 必须证明的结果 |
|---:|---|---|
| 1 | 当前 B1 fix live | production-live 后置 GREEN，当前产品 RED 已消失 |
| 2 | AF5 终态 | `zg361comp.1` authored `42` / native `41`，独立 provider 回读终态；ACK 不算结果 |
| 3 | Central stage 9 | `zg361cl.390` 真实 provider terminal GREEN |
| 4 | Stage 10 玩家可见 manager terminal（机器字段沿用 `central_stage_10_terminal`） | 独立的“AI Central owner → 玩家 F-case subject”路线取得 `zg361mg.120` 真实 provider terminal GREEN；不能从玩家自己的 Stage 9/11 owner 时间线推导 |
| 5 | Central stage 11 | 真实 Workforce provider terminal GREEN（正常 close 或合法 N/A close）；`.361` 宪章/制度债及跨周期后续只作非阻塞 coverage |
| 6 | 代表性终态 cold restore | 真实 save receipt、不同 PID/递增 generation 的 cold restore receipt，以及 B1、AF5、Central、Workforce 的 identity/state/receipt 前后相同回读 |
| 7 | gameplay-window error scan | 完整目标时间窗扫描且 `blocking_diagnostics=[]` |
| 8 | managed cleanup | cleanup GREEN、contract error 为空 |
| 9 | final candidate L0 | 完整 L0 GREEN，tested SHA-256 与待签收 candidate 完全相同 |

九项之外的 source `3/4→4/4`、第三次 `.356`、三次 Workforce 周期、旧 exact `7 action + 4 observation`、全树
definition/场景与 footage 都不能制造 P1 歧义或把 P1 判 RED。它们继续作为带原始状态的 `NON_BLOCKING` coverage/backlog
记录；确有真实 encountered RED 时仍按 SOP 闭环，但不得借此扩张 P1 blocker。历史“四项总门”及其剩余项描述自本节起
`POLICY_SUPERSEDED`。显式 legacy coverage 命令可为自身诊断失败返回 RED；该结果不回写独立 P1 gate。

R326 的当前 source receipt 是
`Z:\ck3_mod_rewrite\_runtime\p2r326incidentsource\phase2-source-capture-three-of-four-v3.json`，SHA-256
`0828ED6F8BD2364145506ED452394B62570F837374086AEE8847420F9D339644`；incident checkpoint 为 `73,156,969` bytes，
SHA-256 `5E9A7687AFAF104CB6B68759F2960BEF85A886EF1908382C50528A5D17BAC550`，原始输入 checkpoint hash 前后不变且 cleanup
GREEN。当前四类 source 中 promotion、projects/metrics、incidents/operations 已完成，**唯一缺项是
`capture_cross_cycle_endgame`**；这是历史 coverage 状态，不是现行 P1 缺项。

`strict 4/361` 与 `definitions 106/626` 只保留为 discovery telemetry：它们不是上述九项 P1 gate，不是 P2 解锁条件，也
不得换算为 T0 剩余百分比。P1 未完成期间，最终宣传视频与宣传工具本轮更新前置都保持硬锁；T0-P2 继续 `LOCKED`。

## 产品与批次用例

| Case ID | 范围 | 核心正例 | 必须保留的反例/门禁 | 当前状态 |
|---|---|---|---|---|
| `P2-L0-001` | 361 manifest | ID 001–361 恰好一次、38 领域、B1–B8 无重叠无遗漏 | 缺号、重复号、错误批次、生成结果漂移即 RED | `STATIC_GREEN` |
| `P2-L0-002` | 脚本/本地化/发布树 | BOM、parser、loc、玩家限定、production allowlist 和生成器 parity | AI 入口、raw key、acceptance-only 泄漏、生成文件手改即 RED | `STATIC_GREEN` |
| `P2-FILE-001` | effect 边界 | 全部 effect 按用途分组，目标每文件 1–10 个 definition | >20 即 RED；例外必须有不可拆理由和精确实机证据 | `STATIC_GREEN / live pending`：626 files / 3721 effects / 最大 10 / 例外 0 |
| `P2-LOAD-001` | 生产 closure | exact CK3 1.19.0.6 加载 hash-bound production tree，唯一产品挂载，loader scan GREEN | frontend/history 超时、Unknown effect/trigger、错误挂载或树漂移即 RED | `LIVE_GREEN`：R101 完整 937-file release-identical 拆分树完成 303/303 database nodes，fatal 0、project match 0；不代表业务长链 GREEN |
| `P2-B1-001` | manager/subject 身份 | manager cycle/case 与 subject ABI 独立，旧存档只读 witness 可见 | subject 字段不得冒充 manager；旧 ticket 不得强行复活 | `LIVE_PARTIAL` |
| `P2-B1-002` | 长期名单与嵌套角色引用 | 每个延迟消费边界剔除不可用 weak Character；每次解引用 Character-valued variable 都重新用外层 `is_alive=yes` 隔离，再读取角色变量 | 产品调用栈出现 `This scope doesn't support variables` 或错误缩小 cohort 即 RED | `LIVE_GREEN`：R100 的 548 日同类窗口中 R99 archive-owner 签名归零 |
| `P2-B1-003` | baseline | 有首府正常结算；无首府时 comparator unavailable 且 delta=0 | 不得把缺值当真实 0，不得读取新 owner 代替冻结对象 | `LIVE_PARTIAL` |
| `P2-B1-004` | 发布链 | 玩家 B1 review 进入 Central，产生 `.146`，选择后 D+1 `.147` 保留 owner/subject/cycle/case | ACK、AI silent summary、fixture flag 不得冒充 source checkpoint | `LIVE_PARTIAL`：R96 已证明 fresh schema-v2 B1 发布并激活 Central；R101 的 stale seed cycle 直到窗口末端 `53160192` 才以 `.200` 开新周期，故 R102 fresh 验证后需同 PID续跑 D+300，而非重启 |
| `P2-B1-005` | 公共上级配额银行跨年与旧存档迁移 | active state `1` 的 schema-v2 bank 在 335 日 deadline 到达前保持原 season/case/state；pre-v2 active manager cycle 无奖励终止并同入口重开；allocator 按 live list size 全量排序 | 新 manager 在公历年变化后不得重建 active bank；旧 case 不得发布/领奖；旧 `.110` ticket 不得冒充新 bank ticket；固定容量不得冒充当前列表长度；filtered range 不得冒充总容器长度 | `LIVE_RED -> STATIC_GREEN / R102 pending`：R101 证明 live `list_size` 后仍有三次 filtered-range RED；两个 mutable-grade filtered walk 已加 `check_range_bounds=no` |
| `P2-B2-001` | 送达/申诉/PIP | 三条真实分支、四次 exact restore、最终 baseline、跨进程 event identity | unset owner、跨 case receipt、申诉加重、资金不守恒即 RED | `LIVE_GREEN`：focused gate；不等于 Phase2 全量 |
| `P2-B3-001` | 管理者/制度 | 上一轮团队快照、京察、校准、PIP/申诉/留任聚合 | 同轮递归、manager/subject 混同、AI 非授权入口即 RED | `LIVE_PARTIAL`：R100 的 548 日窗口中 R99 死亡上司 opinion 签名归零；整域仍待全量长测 |
| `P2-B4-001` | 晋升/职级/现金 | 资格至任命/失败冷却，HC/奖金预留释放，欠付补发守恒 | 失败不释放、跨案串账、玩家/owner 错位即 RED | `LIVE_PARTIAL`：R100 的 548 日窗口中 R99 compensation 与 receipt-revision 签名归零；整域仍待全量长测 |
| `P2-B5-001` | HC/继任/流动/学习 | 真实空缺、候选、现任、backfill、代理、保护期、递延功赏 | 旧案/读档/换上司身份漂移即 RED | `STATIC_GREEN / live pending` |
| `P2-B6-001` | 项目/指标/重组 | 项目贡献与版本、指标分母/窗口、WIP、上线→采用→价值 | 止损自动记差绩效、分母漂移、项目 owner 错绑即 RED | `LIVE_PARTIAL`：R303 已取得 CP #026 receipt 到 P3 #229 metrics 的真实 paused provider 后置条件 GREEN；R313 已冻结对应 CP26 source checkpoint。默认 adapter 仍关闭，且这不等于 B6 全域或完整上线→采用→价值链 GREEN |
| `P2-B7-001` | 事故/运营 | 缺编→工时→外包/招聘→事故→复盘→质量回写长链 | 虚构角色/职位/领地、资金或 HC 不守恒即 RED | `LIVE_PARTIAL`：R326 已冻结真实 `.50` source checkpoint 与 strict receipt；`.190/.290/.390` 的动作后 transition/closure 和整域长链仍待闭合 |
| `P2-B8-001` | 三周期终局 | 目标棘轮、配额回流、经理拒背 C、宪章只改未来默认 | 跨周期身份漂移、追溯改账即 RED | `STATIC_GREEN / live pending` |

## Promotion 长链随机事件合同

这些用例只负责让冻结产品时间轴安全越过独立原版事件，不替代二期业务验收。
可执行用例位于
[`tools/test_zg361_phase2_promotion_source_checkpoint_runner.py`](../../tools/test_zg361_phase2_promotion_source_checkpoint_runner.py)，
运行合同位于
[`tools/zg361_phase2_promotion_source_production_entry.py`](../../tools/zg361_phase2_promotion_source_production_entry.py)。

| Case ID | 正例 | 反例 | 当前状态 |
|---|---|---|---|
| `P2-INT-0399` | `.0399` 精确三 Character + `no_secrets_here` 或 `secrets_to_be_found` 二选一 | 两者同时、错误类型、多余 scope、越界日期 | `STATIC_GREEN / live branch pending` |
| `P2-INT-1002` | `.1002` 前三项为 `0..11` 内递增互异，末项 native 12；选择 authored 13 | 重复、越界、末项错误、receiver 不等于冻结 target | `STATIC_GREEN / next occurrence live pending` |
| `P2-INT-B1200` | `.200` 精确 9/10 或 bank-descendant 13/14 名称集；只绑定事件实际消费的 manager/self-review 九字段，选择 honest option 1 | 少/多 scope、玩家 subject 错位、两个 manager owner 不同、六个消费值类型漂移即 RED；四个未消费 bank payload 不作伪身份断言 | `LIVE_GREEN`：R88 完整字段合同通过并安全选择 option 1 |
| `P2-INT-9006` | `bp1_yearly.9006` 精确一个随机非玩家 courtier、两项 native 0/1；选择只影响玩家自身 piety/stress 的 option 2 | courtier=玩家、多余 scope、选项漂移或同局超过两次即 RED | `STATIC_GREEN / R72 correction live pending` |
| `P2-INT-8080` | `ep3_governor_yearly.8080` 精确一个动态非玩家 magistrate、四项 native 0–3；选择不杀人/不招募/不取金的 punish option 1 | magistrate=玩家、多余 scope、错误日期或选项漂移即 RED | `STATIC_GREEN / R77 correction live pending` |
| `P2-INT-7500` | `health.7500` 精确 root、0 scope、唯一 native 0；不可避免地添加 `fragile_bones` | 任意 scope、额外/缺失 option、日期或 root 漂移即 RED | `STATIC_GREEN / R73 correction live pending` |
| `P2-INT-M001` | 产品 `zg361m.1` 精确 root、3 个 native 0/1/2 选项；选择 reference charter/native 0 | 错误 root、选项漂移；外层遗留 B1 scopes 不得冒充本事件输入 | `STATIC_GREEN / R74 correction live pending` |
| `P2-INT-EXACT` | 已登记事件逐项绑定 date policy、root、typed scopes、完整显示选项与最小副作用路径 | 未知事件或任一字段漂移必须动作前停机 | `LIVE_PARTIAL`；每次 RED artifact 保留 |

## Registry、回归与宣传用例

| Case ID | 交付条件 | 当前计数/状态 |
|---|---|---|
| `P2-REG-001` | promotion `.147` schema-2 source checkpoint；下游 compensation 业务 postcondition 另按 span 门验收 | `1/1`，`LIVE_GREEN`：R294b 已捕获；checkpoint SHA-256 `D4F625C84E900966E0B70CA8FD65CD33D63205B479A3CBC15BC0DF4B02B319F0` |
| `P2-REG-002` | projects `.26` schema-2 source checkpoint；以独立 `.229` provider postcondition 互证同一 contribution receipt | `1/1`，`LIVE_GREEN`：R313 source capture + R303 provider postcondition；R313 checkpoint SHA-256 `72FB7D0F04C8B584555C35AC87313A5581FA8610344F72ABA4758904BC4C433B` |
| `P2-REG-003` | incident `.50` schema-v3 source checkpoint + strict receipt；`.190/.290/.390` 下游业务 transition 另由 B7/postcondition 验收 | `1/1`，`LIVE_GREEN`：R326 checkpoint SHA-256 `5E9A7687AFAF104CB6B68759F2960BEF85A886EF1908382C50528A5D17BAC550` |
| `P2-REG-004` | cross-cycle `.356` + owner `.361` + subject Workforce state | `0/1 / NON_BLOCKING COVERAGE` |
| `P2-REG-ALL` | 上述四项组成 historical canonical registry，路径/字节/SHA/不可变性复核 | `3/4 / NON_BLOCKING COVERAGE`：R326 three-of-four schema-v3 artifact SHA-256 `0828ED6F8BD2364145506ED452394B62570F837374086AEE8847420F9D339644`；cross-cycle/endgame 未采集，但不阻塞 P1 |
| `P2-FULL-001` | 旧 B1–B8 全域矩阵、共享表面抽样与三周期长测 | `POLICY_SUPERSEDED / OPTIONAL COVERAGE`；默认 critical-path runner 不执行此矩阵，只有显式 `--phase2-legacy-full-tree-coverage` 才采样；其中 stage 9–11 另由现行九项硬门独立验收 |
| `P2-R74-ERR` | 已实证的产品运行时错误在同类时间窗归零 | 只看 loader GREEN 或隐藏日志均不得通过；必须扫描完整 gameplay error log | `LIVE_RED -> STATIC_GREEN / R102 pending`：R101 证明单用 live `list_size` 仍不能覆盖迭代内过滤；两个 filtered walk 的范围检查修复需 fresh 同类窗口归零 |
| `P2-CAP-001` | 八个 canonical gameplay spans 均通过 source intake | `0/8 / P2-ONLY`；P1 签收前锁定，不参与 P1 判定 |
| `P2-VIDEO-001` | 人物版完整 build、媒体抽检、双语字幕、安全区、全片审阅、SHA | `0/1 / P2 LOCKED` |
| `P2-VIDEO-002` | 制度群像版独立完成同一套门禁 | `0/1 / P2 LOCKED` |

## 当前执行命令

```powershell
# 静态总门
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\validate_static.py

# Promotion 精确事件与业务 choreography
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\test_zg361_phase2_promotion_source_checkpoint_runner.py
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\test_zg361_phase2_promotion_source_choreography.py

# CK3 启动仍由 run_zhongguo_acceptance.py 串行执行；同一 product/bridge 的连续
# 场景复用受管 session。harness RED 可写 RETAINED receipt 并由独立 client 接续；
# 产品/bridge 变化或最终收口时才要求新启动或 cleanup receipt。
```

每次实机后只更新被真实证据改变的 case。loader GREEN 只更新
`P2-LOAD-001`；原版随机事件被安全排空只更新 `P2-INT-*`；只有业务独立
后置查询完成，才把对应 B 批次或 registry case 升为 `LIVE_GREEN`。
