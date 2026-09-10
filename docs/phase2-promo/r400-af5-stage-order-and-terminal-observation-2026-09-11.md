# R400 AF5 路线勘误与独立终态观测

记录日期：2026-09-11（Asia/Shanghai）。本记录承接[方法论评估](../autonomous-agent-progress/retrospectives/2026-09-11-t0-methodology-review.md)，用户已授权执行。以下为产品源码与历史 artifact 的核对结论；新 AF5 实机验收尚未完成，P1 仍为 1/9，P2 LOCKED。

## 已闭合的归因

R400 的 driver-state 已证明真实 `.147` instance 272 被读取，option 1 被提交，事件随后消失。失败点是等待 `zg361comp.1`，不是源事件未加载。更根本的问题是验收把当前生产阶段顺序写反了：

```mermaid
flowchart LR
  C2[Central stage 2: compensation] --> AF4[AF4: 37 / 36 请求退出]
  AF4 --> AF5[AF5: 42 / 41 结清]
  AF5 --> Done[compensation completed_cycle]
  Done --> C3[Central stage 3: PP]
  C3 --> P147[zg361pp.147]
  P147 --> P148[zg361pp.148: D+1]
```

权威调用链：

- [Central stage 1–3 effects](../../mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_005_stage01_03_effects.txt)：stage 2（159 起）完成 compensation 并核对 completed_cycle；stage 3（242 起）才进入 PP。
- [Central dispatch](../../mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_003_dispatch_control_effects.txt)：完成当前 stage 后自增 stage，D+2 pump。
- [PP event](../../mod_zhongguo_style/events/zg361_feedback_promotion_pip_runtime_events.txt)：`.147` option 1 调用 m147 与 T stage 1 dispatcher；[T stage 1](../../mod_zhongguo_style/common/scripted_effects/zg361_feedback_promotion_pip_003_t_stages_01_effects.txt) 安排 D+1 `.148`，没有反向调用 compensation。

因此旧 split-acceptance 与 choreography 中的 `.147 → comp.1/AF5` 不能作为执行路线。不能通过加长等待、仅推进一天或修改生产业务来迎合它。此处未读取 `.147` 存档的 AF 内部状态，源码阶段顺序不冒充该存档的 native 实测。

## 本轮最短真实路径

选用 `Z:/p2r185promo_a_native_state/profile/save games/autosave.ck3`，77,071,385 bytes，SHA-256 `538175DAE47982CF50623288A4B39738D12A973D6FD61EA3220527D979067000`。

历史 `Z:/p2r192promo_resume/report.json` 记录 AF4 authored/native 37/36 于 date_raw 53183256、AF5 旧 route 1 的 40/39 于 53183280。该输入 header 的同字段为 53181960，距首次 AF5 约 55 游戏日；header 仅作选档诊断，加载后仍通过真实 snapshot/query 确认状态。历史 route 1 循环已由当前产品修复，本轮执行 route 3。

复用既有生产时间线驱动与前十三个 compensation 阶段的 route 1 合同，目标改为 `zg361comp.1` 且 authored 42/native 41 可见、可选。不能只按重复 event key 停靠，也不使用会把 AF4 改为 snooze 的 clean-review recovery override。抵达后读取 AF5 前态，执行 42/41，再独立读取终态并保存 checkpoint。失败保留完整阶段 evidence，健康 paused PID 可继续用于 Python 修复后的重试。

## 为何新增独立 AF5 查询

旧 promotion/compensation 查询要求较晚的 `.147` receipt，并要求 portfolio domain 1–3；AF5 关闭立即将 domain 变成 4，D+1 还会移除 volatile subject/stage/domain。它无法独立证明本轮 AF5 结果。这是已有验收故障的观测缺口。

新增只读 `query_zhongguo_compensation_af5_snapshot_v1`，复用 exact-build character-variable ABI，使用仍保留的 `portfolio_result_subject` 解析 subject；volatile subject 存在时交叉核对。仅发布本次判断所需状态，readiness 表示可观测性，terminal 表示业务终态，二者分别判断。

| 对象 | 终态语义 |
|---|---|
| AF case | state=6、active=0；owner/subject/cycle/case 与前态相同，revision 前进 |
| 最后操作 | operation=300、route=3、repurchase_resolved=1、unit_conserved=1 |
| m299、m300 receipts | active=1、consumed=1、route=3、receipt_state=5；四项 identity 匹配 AF case |
| Portfolio | 即刻 domain=4、visible_pending=0；或 D+1 volatile domain 不再存在且 completed_cycle 对应同一 cycle |

终态依据为 [AF barriers](../../mod_zhongguo_style/common/scripted_effects/zg361_compensation_24_af_stage_barriers_effects.txt)、[AF kernel](../../mod_zhongguo_style/common/scripted_effects/zg361_case_kernel_033_domain_af_lti_grant_effects.txt)、[portfolio apply](../../mod_zhongguo_style/common/scripted_effects/zg361_compensation_07b_portfolio_apply_stage_effects.txt)、[portfolio closure](../../mod_zhongguo_style/common/scripted_effects/zg361_compensation_07e_portfolio_closure_effects.txt)。

身份口径：AF case serial 来自独立 kernel cursor，不等于 portfolio result case serial。查询另读 subject `comp_result_case` 与 portfolio result case 对齐；AF receipts 的 case serial 与 AF case 对齐。两组 identity 的 owner/subject/cycle 一致，但不能错误地把两个 case 编号直接判等。

## 交付边界

本轮不改变产品业务顺序，不扩展 361/626 矩阵。AF5 receipt 按现有独立 P1 gate 签收，不附加 `.147` 源动作。整体业务结果、checkpoint 保存与 cleanup 分别保留；cleanup 成功不覆盖业务 RED。实际 live 结果将在取得后追加，之前只报告源码归因与实现进度。
