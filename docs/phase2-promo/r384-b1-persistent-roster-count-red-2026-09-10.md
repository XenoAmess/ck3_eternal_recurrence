# R384 B1 persistent roster count 产品 RED

## 判决

R384 在固定 400 天 fresh replay 的 D+403 仍停于 B1 state 7。这是产品 liveness RED；不是 harness RED、事件 RED，
也不是观测缺帧。当前修复只达到 `static-ready`，新的唯一 CK3 轮次完成 fresh replay 前不得写 GREEN。

## 不可变实机证据

- 轮次：R384；PID `38864`；connection generation `1`；当时为唯一 CK3 实例。
- 固定窗口：`date_raw 53584920 -> 53594520`；最终只读帧 `53594592`（D+403），未重置、未续期。
- 状态：cycle/case/state=`8/8/7`，active=true，无活动事件。
- 名单：persistent roster=`132`；processing count=`0`；实际 bounded recount=`25/45/10=80`。
- 配额：target=`40/79/13=132`；closure=0；calibration=false；reward=false。
- 账本：amendment/audit=`61/62`；`132/80` 失配与 state 7 已持续 291 游戏日。
- report：`_runtime/p2r383-b1-replay-live/r384-b1-d403-product-red-report.json`，SHA-256
  `D900B9C29E24D7C7759E8B814B316A4BB0B407728606803C25DDFBA66B9C462C`。
- park：`_runtime/p2r383-b1-replay-live/r384-b1-d403-product-red-park.json`，SHA-256
  `768136B6C0896230BD4681E6A69A594A841BED8BC97186B28BBC9FB8C720BC09`。
- driver-state SHA-256 `D4540ABA046B4AD172FEDDAE2A1FFBE2DE68602C9052C0BC8750FB2575F6E63A` 比最终帧旧，
  只用于 lineage，不作为最终产品帧。

原 report 顶层保留的 `pay_homage` typed failure 和 `product_result=NOT_EVALUATED` 是 wrapper 滚动元数据债；
不可变原件不覆写。最终完整 B1 frame 已足以独立判定上述产品 RED。

## 根因

R374 的“同 tick temporary scratch 由 52+80 累计成 132”是中间帧假设，已被本轮完整数据推翻。实际链路为：

1. 冻结 persistent roster 有 76 人，其中 5 个 weak Character row 已失效，正确 retained count 应为 71。
2. prune 用 `list_size:zg361_b1_subjects` 和 `list_size:zg361_b1_processing_subjects` 读取 persistent variable list；
   这两个计数实际落成 0。
3. review backfill 应补 5 人，late join 只剩 4 个容量；但 backfill 未递增 `subject_n`，错误容量门又接纳了全部
   61 名 eligible member，结果为 `71+61=132`，amendment/audit 为 `61/62`。
4. quota 以 132 计算成 `40/79/13`；后续处理链按 80 上限重计成 `25/45/10`，守恒永远无法闭合。
5. 旧存档没有新增 observer `zg361_b1_quota_rebuild_generation`；直接 `change_variable` 产生 empty value-scope 错误。

exact-build CK3 1.19.0.6 的 `game/tests/event_target_lists_tests.txt:217-231`（SHA-256
`E7971460148847A2736CFEFA7032A12B998E220EAC045935083FAD1501974FE8`）对 `add_to_variable_list` 使用
`variable_list_size = { name = test_list_3 value = 1 }` 断言。这证明 persistent variable list 与 temporary
event-target list 的计数接口不同。

## 最小修复与验收目标

- prune/rebuild 时在 owner scope 显式累计原 roster、retained roster 与 processing roster。
- 每次成功 backfill 或 late join 都递增 `zg361_b1_subject_n`，让 80 人容量门真实生效。
- generation 已存在时递增；旧存档缺失时显式 materialize 为 1。
- band ordered max 使用已显式计算的 `zg361_b1_band_middle_n`，不再读取 persistent list_size。
- 结算 scoreboard 使用 `ordered_in_list variable = zg361_b1_subjects`；R386 进一步证明上限必须钳制到当前
  `zg361_cohort_n`（最高 80），不能向短于 80 的持久名单提交固定 `max=80`；不再以 temporary-list
  selector/size 读取持久 roster；否则 state 8 后仍可能发布空榜单。
- 不重写 quota 架构；commit `95f6824` 的 temporary-list 清理作为独立防回归保留。

静态预期链：`76 - 5 + 5 + 4 = 80`；amendment/audit=`14/15`；quota=`24/48/8`。已通过 generator
`--check`、B1 normal/`-O` `76/76`、quota model normal/`-O` `74/74`、MCP B1 contract normal/`-O`
`13/13`、本地静态校验及 release build/check。fresh replay 必须在同一 checkpoint、同一固定窗口中证明上述值并进入
state 8，才能关闭 RED。

本修复改变 CK3 游戏脚本，因此不能在 R384 热恢复。提交推送后须由 operator MCP 受控清理 R384，确认 CK3=0，
再以递增新轮次独占启动。公共 MCP schema/API/ABI 未变，open_kaishek 无代码同步需求；P1 未签收，P2 视频锁不变。
