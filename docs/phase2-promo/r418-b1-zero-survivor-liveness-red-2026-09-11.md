# R418 B1 零幸存者 liveness RED

## 判决

R418 attempt 06 已在同一 CK3 PID 和 connection generation 内解除全部已知原版事件阻断，并把固定的
`10190` 天产品观察窗跑到绝对截止点。Central 与 standalone PP 始终没有启动；直接原因是玩家的 B1 经理对象从窗口起点到终点
一直停在 active/state `7`，其冻结 roster 与 processing 域均为 `0`，也没有 pending、reopen 或隔级回调可以重新进入 closure。
继续延长窗口不会增加信息，故本轮判为 **production liveness RED**。

这与 R386 的“还剩 73 个 survivor、最后回调前需压缩并重封”不是同一状态。R418 已经没有 survivor，也没有回调。不能发布一个
空结果来伪造 B1 GREEN；正确恢复是无奖励、无发布地退役该旧周期，再由已经存在的玩家年度请求从当前 live vassal 域打开新周期。

## 不可变实机证据

- 轮次：R418 attempt 06，PID `204536`，connection generation `1`，玩家 `32904`。
- 固定观察范围：retained origin `53905680`，absolute deadline `54150240`；实际失败帧 `54150408`。
- B1 同一暂停帧：cycle/case `8/8`，state `7`，open year `1116`，runtime schema `2`，active `true`。
- roster：subject/before-prune/pruned `0/0/0`，amendment/audit `61/62`，reopen-required `false`。
- processing：count `0`，但旧 agenda/local-candidate/pre-calibration-valid 仍为 `132/132/132`。
- quota：book `2`，target `40/79/13`，recount `25/46/9`，pre-calibration expected `133`，mismatch `true`；
  `quota_rebuild_generation` 缺失。
- closure：state `0`，calibration-finalized/rewards-issued/publication-blocked 均为 `false`。
- pending：open/slot/expected/paid 均为 `0`，committed `false`，watchdog 字段不存在。
- 观察期间 20 次 timeline interrupt drain 均 GREEN；每次 product progress 仍为
  `b1_active=true / review_now=false / central=false / pp=false`。Stage 指针虽为 `9`，Central 因 B1 未发布而不可达。
- 汇总 artifact：
  `_runtime/p1-terminal-resume-r418-20260911/live-artifacts/terminal-stages-red-attempt-06.json`，
  `1,130,607` bytes，SHA-256
  `999828C356E88EB943A9E4CC22ACBF63BA294AFBAAFCA83FAE750C67D3342B76`。

同一 artifact 也闭合了 `tgp_movement_events.0070` 的第二次合法实例：authored `1` / native `0`，instance
`1108 -> null`，snapshot `native:2692 -> native:2693`，revision `2693 -> 2694`，
`postcondition_verified=true`。这项结果只把该原版事件合同升级为 production-live primitive；它不改变 B1 RED。

## 根因与生产唤醒缺口

现有恢复链各自覆盖了相邻状态，但没有覆盖 R418 的终态：

1. D+340 manager watchdog 只在 state `6` 重开 calibration；R418 已在 state `7`。
2. pending watchdog 只在 `pending_open_n >= 1` 时推进；R418 为 `0`。
3. final-survivor compaction 要求 closure `1`、reopen barrier 已消费且至少还有可重封的 processing 域；R418 为 closure `0`、
   processing `0`。
4. 年度京察请求与 common-superior sibling 请求都会因为 `zg361_b1_serial_dependents_active_trigger` 看到 active B1 而持续轮询，
   却没有在判 busy 之前修复这个 callback-free 状态。

因此根因不是观察时间不足，也不是新的原版事件合同，而是 B1 在最后一个 weak Character row 消失后缺少 manager-owned
零幸存者恢复入口。

## 最小修复合同

生成器新增 `zg361_b1_recover_empty_calibration_cycle_effect`。它只在现有玩家请求边界运行，并要求全部条件同时成立：

- `is_ai = no`、active flag、runtime schema `2`；
- state `7`、closure `0`、calibration 未 finalized；
- pending open `0`、oversight return `0`、publication 未 blocked；
- quota built serial 与当前 manager case 完全一致；
- Character-safe prune 后 subject 与 processing 均为 `0`。

命中后记录 recovery cycle/case/year，把遗留列表和计数清零，将旧周期置为 inactive/state `8`，保留 rewards 为 `0`，移除
open-year 与 review flags，并明确不调用 `zg361_b1_mark_published_effect` 或结算发奖。调用者随后在同一请求中重新检查 serial busy；
若 Central/PP 也未占用 serial，就调用既有 `zg361_b1_open_cycle_effect` 从当前 live vassal 域开启新周期。

唤醒点覆盖年度首次请求、既存 `.42` 两日轮询票据、common-superior `.90/.91` 请求以及 review-now bridge；
`open_cycle` 本身也在 eligibility 检查前调用恢复，避免其它合法玩家入口绕过。没有新增 on_action、console、fixture、AI 入口或公共 MCP/ABI。

## 当前验收边界

- B1 generator 生成 24 个文件并通过 `--check`。
- B1 runtime normal/`-O` 各 `76/76` GREEN。
- `validate_local.py` normal/`-O`、根 `validate_static.py` GREEN。
- ZhongGuo release tests `9/9` GREEN；1,031-file 可复现 release manifest / ZIP SHA-256 为
  `63443F986F873924B4B0AB4D17C32D052CE1E83A8A5A2836D4D83370F12B9B2B` /
  `647AB1A16941955536A5303E587516275B7A00319B1F2F1CABA107D8E9ECFE25`。
- 原版事件合同测试 `288 passed, 775 subtests passed`；portable evidence 为 `271` blobs / `1063` refs，
  manifest SHA-256 `EEF35766EF2E4C45EC834E3437C5D4769DD550309223472D7F49DC7D6BA48DA8`。

修复当前严格是 `static-ready`。游戏脚本无法热加载到 R418；必须先受控清理旧 PID，再以包含本修复的新 production projection 和
fresh CK3 进程恢复同一冻结 checkpoint。live 升级至少要证明旧 cycle/case `8/8` 被退役、新 serial 被打开，并最终获得无 anomaly 的
B1 state `8` / closure `4` / finalized，再恢复 Central 9–11 的正式 terminal 验收。T0 保持 `50% / stage 8/11 / P1 未签收`，
P2 视频继续锁定。
