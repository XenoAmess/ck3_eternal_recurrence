# R589–R593 四段 take、`.8030` 实机闭环与 Central 总结恢复（2026-09-13）

## 验收状态

- T0 P1 保持 `9/9 GREEN`，本轮没有重跑或改写 P1。
- T0 P2 保持 `0/8`。本次 take 只完成前四段，不能把局部 clean span 计入正式八段分母。
- 最终宣传片硬锁继续生效；本轮只采集候选源录像，没有制作、更新、发布或预热最终视频。

失败 take 位于：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r589-plus-e415830-20260913`

关键证据：

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `423AB6354B0EAAFF9E74C3A870C18AB08AE49607C67B157D33FF86043C5A6F1D` |
| `capture/report.json` | `6D413E3DE4AC1782457E372A5917BB27FC177D288DFDBED5B8E063452C4B263A` |
| `capture/cell/phase2_promo_phase2_hc_workforce_mature_endgame_source_zg361we_360_native_event_wait_gate.json` | `CDBBF4140333E25B7B2A7533BE589DBAB50DA3E3E86C1DA1343D41EDF426D2C1` |

## 单实例轮次与录像结果

| 轮次 | PID | 用途 | 处置 |
|---|---:|---|---|
| R589 | `94616` | frontend warmup | Frontend GREEN 后终止，清理已证明 |
| R590 | `159812` | gameplay，段 1–2 | 为 manager source 切换而终止，清理已证明 |
| R591 | `170688` | manager governance，段 3 | 为 promotion source 切换而终止，清理已证明 |
| R592 | `145892` | promotion compensation，段 4 | 为 HC source 切换而终止，清理已证明 |
| R593 | `45076` | HC/Workforce mature source | 遇到 `zg361p2c.2` RED 后终止，清理已证明 |

同一 FFmpeg 录制进程 PID `45380` 覆盖整次 take，并在收口时停止。原始候选为：

`capture/cell/promo/raw/zg361-promo-live-full-take-01.mkv`

其大小为 `290,584,880` bytes，SHA-256 为
`D4B3322B78EDB00AB2FD39B0B2DC6E183447A67D1BF0EDE58835376A250286A8`。时间线已经得到四组成对 clean marks：

1. `phase2_fact_quota_calibration`
2. `phase2_receipt_appeal_pip`
3. `phase2_manager_governance`
4. `phase2_promotion_compensation`

缺失的四段为 `phase2_hc_workforce`、`phase2_projects_metrics`、
`phase2_incidents_operations` 和 `phase2_cross_cycle_endgame`，因此
`clean_capture_complete=false`。报告耗时 `680.066 s`。最终 inventory 复核为 CK3 `0`、FFmpeg `0`；R589–R593 均为旧轮次且已经终止。

## `.8030` 实机闭环

R593 在恢复成熟 `.356` 来源、选择 authored 1 后先遇到
`ep3_story_cycle_admin_eunuch.8030`。上一工作包的共享原版合同在这次真实 paused frame 上全部通过：

- `date_raw=53366664`，event instance `621`，root/player `32904`；
- snapshot authored count `4`，实际可见 native 映射 `0, 1, 3`；
- context、schema/version、root、完整 scope 名称/类型、option variant 与 selected mapping 检查全部为 `true`；
- 实际提交 authored option `4` / native index `3`；
- postcondition 为 `event_instance_advanced`，旧 instance `621` 不再保留；
- 玩家压力保持 `58`，gold raw 保持 `1434963781`。

这把 `.8030` 从静态合同提升为本次 exact build 上的真实 paused-live GREEN。共享原版事件知识资产继续使用同一合同，没有复制第二份事件定义。

## 新 RED：`zg361p2c.2`

`.8030` 关闭后，时间线在 `date_raw=53366688` 出现产品事件
`zg361p2c.2`，event instance `622`，唯一可见按钮为 authored 1/native 0。等待器保持
`clear_unexpected_single_option_events=false`，所以没有盲点按钮，而是以以下原因收口：

`unexpected event blocks native phase-two path: zg361p2c.2 options=1; single-option auto-clear=False`

该事件是 Central 在 Workforce status 已关闭并记录 stage 11 后排队的唯一玩家可见汇总。生成源只读取
`zg361_p2c_summary_cycle` 与 `zg361_p2c_summary_case` 两个 value scope；唯一按钮清除
`zg361_p2c_summary_pending`，随后消费待处理的年度监察结果。其既有严格合同位于
`tools/zg361_phase2_promotion_central_contracts.py`，历史 R200 及 manager-recovery 回归已经证明 1/0 路线。

将 R593 实帧直接送入现有解析器后，玩家根重绑、日期窗口、event identity、两个消费 scope 的类型、snapshot option count、完整 authored option shape 和 selected mapping 全部通过。RED 根因是当前 P2 wait 只尝试共享原版注册表；它没有调用已经存在的 Central 产品合同，并非 mod 事件实现故障。

## 最小修复与验证

代码提交并推送为：

`e2dbf758ca5f735625a0f45caefd917205847f29` — `Handle reviewed P2 central summary interrupt`

修复内容：

- 抽出原版与产品共用的严格 timeline drain 核心，继续复用已有
  `_resolve_timeline_interrupt_contract` 与 `_drain_known_timeline_interrupt`；
- 为 P2 choreography 增加显式 reviewed-product 开关；
- 产品允许集只取 `CENTRAL_TIMELINE_CONTRACTS`，当前唯一条目是 `zg361p2c.2`；
- 原版和产品决策分别写入 evidence，保留合同来源；
- 通用单按钮自动清理仍为 `false`；未知产品/原版事件、scope 漂移、option 漂移或 postcondition 失败仍在选择前后保持 RED。

聚焦验证：

- reviewed wait：normal `4/4`、optimized `4/4` GREEN；
- P2 event choreography：normal `23/23`、optimized `23/23` GREEN；
- Central/manager-recovery contracts：normal `67/67`、optimized `67/67` GREEN；
- R593 实帧的现有合同重放检查：全部 `true`；
- `py_compile` 与 `git diff --check`：GREEN。

本包只改 Python runner 和聚焦测试，没有改 mod 产品树、DLL、游戏文件、启动配置、加载顺序或 MCP schema/version。它没有改变 T0/T1 对外接口，不触发 open_kaishek 兼容层更新；MCP 通用资产只复用了既有只读事件上下文与严格合同执行器。

## 下一步

下一次只执行一轮新的连续八段 P2 source capture。新 CK3 启动从 R594 warmup 开始，随后 R595 gameplay；启动前必须再次确认没有其他 CK3 实例。若再次出现新 RED，继续在实际阻点处停止并做最小合同或产品修复，不扩成单 bug 长跑、全库事件审计或无关验收。
