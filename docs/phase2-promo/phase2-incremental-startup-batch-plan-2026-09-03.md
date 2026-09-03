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

## 条件性 workforce 二分

workforce 有 324 个顶层 block、约 4.64 MB；静态扫描还发现跨域 callable 和高入度 generated mechanism helper。若 checkpoint 7 失败，不截断 block、不修改生产文件，而是在同一个 old-core + 已闭合依赖基线上按完整 block 边界递归二分，最多保留 3–6 个诊断轮次。每轮都要记录新增文件清单、树 SHA、首个日志 marker 和内存曲线。

## 每轮硬门

- 离线 Gate A：累计 product 的文件数、字节数、tree SHA 与 materializer 报告完全一致；projection 名称和 manifest SHA 一致。
- 离线 Gate B：从 known-good profile 复制全新 disposable userdir；settings SHA、shadercache 数量/字节/tree SHA 一致；不得复用已启动目录。
- CK3 只能单槽串行。完整 GREEN 至少要看到窗口、`Frontend`、`End loading of history`、200 heartbeat、exit 0 和 cleanup；`Frontend` 与 history 到达即可记为 `STARTUP_GREEN`，未收到 heartbeat 只标为 observer RED，不倒推 CK3 启动失败；若 `error.log` 有 parser/projection symbols，再叠加 `PARSER/PROJECTION_RED`。
- 任何目标/源码快照不配套（例如旧冻结 runner 不支持命名 projection，或 autoplayer 缺少 runner 所需常量）都记为 `INVALID_TARGET/PREFLIGHT_RED`，不计作 CK3 失败，也不启动错误目标。
- 失败 attempt、日志、report 和 SHA 保留，不被后续 GREEN 覆盖。

## 当前状态

- 13 个累计 product tree 已离线生成，0–12 的 A/B 静态门均 GREEN；最终 broad 目标为 279 files / 29,351,046 B。
- 历史 old-core、部分 core/case-kernel 组合有 Frontend/clean-exit 证据；30 分钟 monolith control、workforce monolith 和 B7 stub 仍停在 `Total of : 881`，尚未形成完整 history 证据。c91 的 batch01 `core-current` 则已于 15:04:20 到达 `Frontend` 与 `End loading of history`。
- checkpoint 1（`core-current`）的 c91 实测已实际启动 CK3：启动层为 `STARTUP_GREEN`，但整体 report 仍为 RED，decision 仅为 observer coverage 的 `heartbeat_not_observed`；`error.log` 有 176 行 projection-missing symbols（含 `Unknown effect`/trigger 等），故分类为 `STARTUP_GREEN / PARSER-或-PROJECTION_RED`，不是 CK3 启动失败。报告为 `Z:\\ck3_mod_rewrite\\_runtime\\formal-phase2-incremental-01-core-current-c91-20260903\\artifacts\\runner-report.json`，SHA-256 `1371E0C601253C555EF46DB5315779017D9BA278957C7BA88ED69D6726EA423B`。旧 `4ff` preflight RED 仍为 `ck3_launch_attempted=false` 的启动前源码配套问题，不计作 CK3 失败。
- 用户取消了 7200 秒续测；后续沿用原有短诊断窗口，首失败即保存证据并进入窄二分，不再无条件等待两小时。

## 预计时间

离线物化/预检通常数分钟。使用已 warm 的有效 profile 时，单次 CK3 边界约 2–5 分钟；若遇到 300 秒无进展的加载边界，立即封存并转二分。17 个固定 checkpoint 的理论观察窗口约 35–85 分钟，workforce 条件轮再加约 6–30 分钟；实际以首失败位置为准。完成首个有效 checkpoint 后再更新剩余 ETA。

本计划只负责定位二期加载边界；seed、8 段 clean footage、两版宣传片仍须在闭包通过后另行验收。宣传工具在开始视频制作前必须再次确认 `origin/main` 最新版本。
