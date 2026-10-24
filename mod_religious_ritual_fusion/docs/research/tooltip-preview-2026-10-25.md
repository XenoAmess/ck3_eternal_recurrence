# 决策 tooltip 预演：R0006 复现与存在性守卫

`machine_id: 4-8e1c2f1861`。本轮只读观察时间为 `2026-10-24T22:31:50Z`–`22:33:20Z`（本地日期 2026-10-25）。身份由本轮 `python tools/ck3_live_run_id.py machine` 读回。源码基线为 `5f4c1043888f24f4caaa6c3f6264614546ccf30c`；研究时 Root 已在工作树加入下述单文件守卫，尚未实机验证。本报告没有启动游戏、操作屏幕、修改 runtime 或执行构建。

结论：`hidden_effect` 不能隔离 effect 的 tooltip 求值。应在前序写入之后，用独立 `if.limit` 仅检查变量是否存在，再进入读取这些变量的整个子链。当前 RRF 改动状态为 **static-ready**；不能据原版先例或通用 parser 结果追认为引擎修复通过。

## 原版直接证据

以下相对路径均以本机实际安装的 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game` 为根，仅证明该机器读取到的文件。

| 原版文件 | 行号和实际结构 | 全文件 SHA-256 |
| --- | --- | --- |
| `common/scripted_effects/00_intrigue_perk_effects.txt` | 13–30：缺少两个计数变量时先 `set_variable`；35–43：作者明确说明 tooltip 阶段前面的初始化不会创建变量，因此先用 `has_none_of_variables` 输出静态提示；44–49 的 `else_if` 才读取变量。 | `ca094d3ee65b6aa29901a61c56ea2a2ad008b7b5673a4e598584378e2429643a` |
| `common/decisions/00_artifact_decisions.txt` | 525–530：在 `hidden_effect` 内创建并保存 `local_artisan`；540–545：另一个 `hidden_effect` 中仍以 `if.limit = { exists = scope:local_artisan }` 保护访问。542 的注释明确说明，这是避免 tooltip generation 假阳性，实际执行时该 artisan 应当存在。 | `79dd6ef37068abec68fcf5155aa23eed8ac6ea957352ba319dfdc4ea42b0a641` |

第二例直接否定“加上 `hidden_effect` 就不会进入内部求值”的假设。第一例与本次“前序设置变量、后序读取未设置变量”的原因一致。这里需要的是带分支体的惰性边界，不能把 `has_variable` 与实际 `var:` 读取并列放进同一个 trigger 列表，然后依赖书写顺序。

补充原版证据：`common/decisions/dlc_decisions/ep3_decisions.txt:2532–2539` 同样在 `hidden_effect` 内以 `exists = scope:local_artisan` 保护访问，SHA-256 为 `fd26051062de094fd537ab0d680141c0ef113d396578856d99f3fb2415656cd0`。`common/decisions/00_lifestyle_decisions.txt:400–411` 将展示的 prestige／文本置于 `show_as_tooltip`，另行触发实际事件；该用法不能作为禁止内部预演的证据，文件 SHA-256 为 `3110c1f0398721a69fe24d68415222f48e886fe6c263d92902facdf8c7bb604a`。

本轮对安装目录 `common`、`events` 搜索 `is_tooltip`、`is_in_tooltip` 等候选，仅找到教程检测已打开 tooltip 的相关用法，没有找到可用于区分本次 effect 执行／预演的正式条件。因此没有引入未经证实的 `is_tooltip = no`。这不等于证明二进制中绝不存在其他机制。

项目既有[语法踩坑](../../../docs/grammar/pitfalls.md)第 210–212 行记载同块前序写入、后序读取在 tooltip 阶段失效；第 352 行还记载 `hidden_effect` 中的 `trigger_event` 会追入事件 `immediate`。换一层事件本身不能修复该问题。本次不新增 pending GUI 或执行框架。

## R0004 到 R0006 的实际结果

R0004 已显示实际草稿窗口，但预演产生 unset `rrf_source_a`，三个日志累计约 204 MB；未最终确认融合。`7cb318d025ca7af253303176525138a94f8f2207` 在两项入口决策采用静态提示加 `hidden_effect`，随后 R0006 的实际源码 `5f4c1043888f24f4caaa6c3f6264614546ccf30c` 仍重现同类错误。因此旧方案没有解决 tooltip 求值，不能继续称为已修复。R0004 的实际记录见[准备与实机记录](../acceptance/preparation-2026-10-25.md)对应场次段落。

R0006 证据根为 `C:/workspace/rrf-development-20261024`，run 为 `4-8e1c2f1861--religious-ritual-fusion--R0006`。事前 `root-execution-a06/PREVIEW-LOGS.before.actual.json` 记录观察时间 `2026-10-24T22:17:23.423033+00:00`，每日志增量上限 1,048,576 B、合计上限 2,097,152 B；该回执 SHA-256 为 `d398de7f54de988b2e3cd2a37be7ed2c0726637b047bed5d80250d2af8d6a520`。

本轮只读 `managed-states/core-rite-a06/state/profile/logs/error.log` 的事前 offset 19,347 后首段，实际首条新增 RRF 错误为：

```text
[06:19:38] Script system error! (while building tooltip/description)
Error: Failed to fetch variable for 'rrf_source_a' due to not being set
rrf_draft_effects.txt:52 (rrf_prepare_draft_effect)
  -> rrf_draft_effects.txt:28 (rrf_open_rite_effect)
  -> rrf_decisions.txt:36 (rrf_begin_rite_fusion_decision:effect)
```

紧随其后是第 53 行的 `rrf_source_b` 缺失，再进入 `rrf_catalog_initialize_00.txt:7`，经 dispatch:5、draft:54 返回同一入口。这是同一依赖链被预演的实际错误；日志时钟按原文保留，不将其转换为主机 UTC。

| 日志 | 事前 bytes | 本轮只读观察 bytes | 增量 bytes |
| --- | ---: | ---: | ---: |
| `error.log` | 19,347 | 67,658,041 | 67,638,694 |
| `debug.log` | 1,124,297 | 68,763,136 | 67,638,839 |
| `game.log` | 20,717 | 67,659,411 | 67,638,694 |
| 合计 | 1,164,361 | 204,080,588 | 202,916,227 |

三项及合计均超事前预算，结果 **RED**。该场没有执行最终融合提交，没有新的融合成功证据。本轮没有复制或完整导出这些大日志；只读事前回执、限定错误片段及文件大小。

## 最小生产改动与相邻入口检查

Root 已将 `common/scripted_effects/rrf_draft_effects.txt:55–66` 改为下述结构；研究时全文件 SHA-256 为 `1ee46abb79087bffb2d5be95cf6c2d90fb2143960ddbb31fa660e122157e75a4`：

```text
if = {
    limit = {
        has_variable = rrf_source_a
        has_variable = rrf_source_b
        has_variable = rrf_source_a_faith
        has_variable = rrf_source_b_faith
    }
    var:rrf_source_a = { rrf_collect_core_candidates_effect = yes }
    var:rrf_source_b = { rrf_collect_core_candidates_effect = yes }
    rrf_catalog_initialize_doctrines_effect = yes
    rrf_refresh_validation_effect = yes
}
```

此前的真实四项 `set_variable` 保留。没有创建假来源、默认 Rite 或伪成功状态。守卫保护 A／B core 收集、整个 doctrine catalog 初始化及 validation，不只保护最先报错的两个上下文切换。缺少前序写入的预演应当跳过读取；真实执行落实写入后应当进入。这两个“应当”仍需同一真实路径核验。

相邻入口只读检查结果如下，未扩大产品修改：

| 入口 | 实际调用与顺序依赖 | 本轮结论 |
| --- | --- | --- |
| 打开 Rite／Faith 草稿 | `rrf_draft_effects.txt:28/40` 均进入同一 prepare；prepare 内 catalog 和 refresh 现在一起受四变量守卫。 | 同一个最小修复覆盖两个模式的该依赖点；R0006 仅提供 Rite 入口的失败复现。 |
| 核心／教义选择及刷新 | `rrf_scripted_guis.txt:33–43,99–102` 以 effect 调用 selection／refresh；GUI `rrf_fusion_window.gui:178–179,283–284,319–320` 使用点击 `Execute` 与条件 `IsValidTooltip`。`rrf_selection_effects.txt:36–66` 仍有 count 初始化、累计和 catalog 验证顺序依赖。 | 未发现决策另有直接进入这些 effects 的旁路。草稿实际存在后使用持久来源。不能由此宣称这些 effects 可被完整 effect-tooltip 预演，下一真实选择／刷新仍需检查日志。 |
| 提交／结果完成 | `rrf_commit_effects.txt:4–9` 刷新并检查 ready；52–73 的 capture 先写 core_index，再逐项读取／累加；22–25 用独立 `exists = scope:rrf_new_rite` 分支保护创建后对象。完成流程读取真实 draft 来源。GUI `rrf_fusion_window.gui:149,187–188` 的提示读取 `is_valid`，点击才 `Execute`。 | 提交有自己的顺序依赖；本轮没有点击确认，也未取得其效果预演或业务完成证据。不要将这些 helper 加进新的决策效果描述。仅凭当前检查不追加无实证的大范围 guard。 |

`rrf_draft_current_trigger` 自身也包含存在性检查和变量比较；同级 trigger 条件不构成这里证明的惰性边界。本次依靠外层 effect `if` 先截断缺来源的首次 prepare 链，并不声称这个 trigger 已独立获得“无来源也安全”的认证。

## 下一次真实回归与预验边界

按既有原生路线重新执行目标选择器 → Next → 决策 Confirm → 生产草稿；点击前记录三份日志的实际身份、offset 和预定增量预算，点击后确认新增片段没有 RRF tooltip script error 且各项／合计均在预算内。还必须核真实草稿来源与候选数据确已初始化，避免把跳过实际初始化误认为修复成功。随后真实 toggle、doctrine 选择、refresh、最终提交分别检查新增日志和业务后态；ACK、窗口出现或 Maven 通过均不能替代这些断言。当前报告没有执行该回归。

现有 [implementation status](../implementation-status-2026-10-24.md) 的 open_kaishek 证据是通用 corpus parser，工具工作树 commit `2b559966c72f4e845111e3e15652ae2354aaed57`；其回执明确没有 CK3 1.20 宗教融合语义 profile。通用语法检查不能模拟 effect tooltip 的惰性与写入物化，不能覆盖本次引擎行为。本轮不复跑旧 corpus、不新增测试框架；正式 Maven／staging 检查和下一场引擎结果另行记录。
