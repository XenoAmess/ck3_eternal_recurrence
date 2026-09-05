# 天朝二期验收用例索引

状态：**滚动维护；主体内容已进入生产候选，但全量实机回归尚未完成**。

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
- 四类 registry 与八段素材边界：
  [`final-promo-non-ck3-prep-audit-2026-09-04.md`](final-promo-non-ck3-prep-audit-2026-09-04.md)

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

## 产品与批次用例

| Case ID | 范围 | 核心正例 | 必须保留的反例/门禁 | 当前状态 |
|---|---|---|---|---|
| `P2-L0-001` | 361 manifest | ID 001–361 恰好一次、38 领域、B1–B8 无重叠无遗漏 | 缺号、重复号、错误批次、生成结果漂移即 RED | `STATIC_GREEN` |
| `P2-L0-002` | 脚本/本地化/发布树 | BOM、parser、loc、玩家限定、production allowlist 和生成器 parity | AI 入口、raw key、acceptance-only 泄漏、生成文件手改即 RED | `STATIC_GREEN` |
| `P2-FILE-001` | effect 边界 | 全部 effect 按用途分组，目标每文件 1–10 个 definition | >20 即 RED；例外必须有不可拆理由和精确实机证据 | `STATIC_GREEN / live pending`：626 files / 3721 effects / 最大 10 / 例外 0 |
| `P2-LOAD-001` | 生产 closure | exact CK3 1.19.0.6 加载 hash-bound production tree，唯一产品挂载，loader scan GREEN | frontend/history 超时、Unknown effect/trigger、错误挂载或树漂移即 RED | `LIVE_GREEN`：R88 完整 936-file release-identical 拆分树完成 303/303 database nodes，fatal 0；不代表业务长链 GREEN |
| `P2-B1-001` | manager/subject 身份 | manager cycle/case 与 subject ABI 独立，旧存档只读 witness 可见 | subject 字段不得冒充 manager；旧 ticket 不得强行复活 | `LIVE_PARTIAL` |
| `P2-B1-002` | 长期名单与嵌套角色引用 | 每个延迟消费边界剔除不可用 weak Character；每次解引用 Character-valued variable 都重新用外层 `is_alive=yes` 隔离，再读取角色变量 | 产品调用栈出现 `This scope doesn't support variables` 或错误缩小 cohort 即 RED | `LIVE_GREEN`：R88 跑满同类 550 日窗口，产品 weak-variable 调用栈为 0 |
| `P2-B1-003` | baseline | 有首府正常结算；无首府时 comparator unavailable 且 delta=0 | 不得把缺值当真实 0，不得读取新 owner 代替冻结对象 | `LIVE_PARTIAL` |
| `P2-B1-004` | 发布链 | 玩家 B1 review 进入 Central，产生 `.146`，选择后 D+1 `.147` 保留 owner/subject/cycle/case | ACK、AI silent summary、fixture flag 不得冒充 source checkpoint | `BLOCKED`：R88 已实机到达 B1 publication 与 Central hook，但聚合日志不能证明属于玩家；550 日内仍无 `.146/.147`。R89 已静态锁定逐观测的 player-owned B1/Central/PP 时间序列 |
| `P2-B2-001` | 送达/申诉/PIP | 三条真实分支、四次 exact restore、最终 baseline、跨进程 event identity | unset owner、跨 case receipt、申诉加重、资金不守恒即 RED | `LIVE_GREEN`：focused gate；不等于 Phase2 全量 |
| `P2-B3-001` | 管理者/制度 | 上一轮团队快照、京察、校准、PIP/申诉/留任聚合 | 同轮递归、manager/subject 混同、AI 非授权入口即 RED | `LIVE_PARTIAL` |
| `P2-B4-001` | 晋升/职级/现金 | 资格至任命/失败冷却，HC/奖金预留释放，欠付补发守恒 | 失败不释放、跨案串账、玩家/owner 错位即 RED | `STATIC_GREEN / live pending` |
| `P2-B5-001` | HC/继任/流动/学习 | 真实空缺、候选、现任、backfill、代理、保护期、递延功赏 | 旧案/读档/换上司身份漂移即 RED | `STATIC_GREEN / live pending` |
| `P2-B6-001` | 项目/指标/重组 | 项目贡献与版本、指标分母/窗口、WIP、上线→采用→价值 | 止损自动记差绩效、分母漂移、项目 owner 错绑即 RED | `STATIC_GREEN / live pending` |
| `P2-B7-001` | 事故/运营 | 缺编→工时→外包/招聘→事故→复盘→质量回写长链 | 虚构角色/职位/领地、资金或 HC 不守恒即 RED | `STATIC_GREEN / live pending` |
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
| `P2-REG-001` | promotion `.147` checkpoint + 独立 postcondition，同 lineage/owner/cycle/case | `0/1` |
| `P2-REG-002` | projects `.26` source + `.229` postcondition | `0/1` |
| `P2-REG-003` | incident `.50` + `.190/.290/.390` instance transitions | `0/1` |
| `P2-REG-004` | cross-cycle `.356` + owner `.361` + subject Workforce state | `0/1` |
| `P2-REG-ALL` | 上述四项组成 canonical registry，路径/字节/SHA/不可变性复核 | `0/4`，`NOT_RUN` |
| `P2-FULL-001` | B1–B8 production projection 一次启动、共享表面抽样、三周期长测、release staging | `NOT_RUN`；不得用 focused GREEN 代替 |
| `P2-R74-ERR` | R74/R78 实证的产品运行时错误在同类时间窗归零 | 只看 loader GREEN 或隐藏日志均不得通过；必须扫描完整 gameplay error log | `LIVE_GREEN`：R88 同类 550 日完整 gameplay error log 中 weak-scope、ordered-list、local-rank、旧事件/本地化签名均为 0 |
| `P2-CAP-001` | 八个 canonical gameplay spans 均通过 source intake | `0/8` |
| `P2-VIDEO-001` | 人物版完整 build、媒体抽检、双语字幕、安全区、全片审阅、SHA | `0/1` |
| `P2-VIDEO-002` | 制度群像版独立完成同一套门禁 | `0/1` |

## 当前执行命令

```powershell
# 静态总门
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\validate_static.py

# Promotion 精确事件与业务 choreography
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\test_zg361_phase2_promotion_source_checkpoint_runner.py
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\test_zg361_phase2_promotion_source_choreography.py

# CK3 实机由 run_zhongguo_acceptance.py 的专用 mode 串行执行；每个 run 使用
# 独立 artifacts-dir / userdir / pipe，完成后必须有 cleanup receipt。
```

每次实机后只更新被真实证据改变的 case。loader GREEN 只更新
`P2-LOAD-001`；原版随机事件被安全排空只更新 `P2-INT-*`；只有业务独立
后置查询完成，才把对应 B 批次或 registry case 升为 `LIVE_GREEN`。
