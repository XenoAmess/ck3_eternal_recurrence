# M6 意见刷新修复的自然采用

机器 `xenoamess-full-tower-eb9d2c1186`；核读时间 `2026-10-19T07:28:49Z`。只消费 runtime owner 明示 closed 的 AUTO551、自然结果小投影及冻结 sidecar，所有大小、SHA、指针和时点见[事实包](evidence/g2-m6-opinion-refresh-actual-2026-10-19.json)。

C7 business source `8e1e59f073f239d266f5b59f57c65b5645658512` 的实际行为已确认：原 AUTO48 的 action、actor31254→33946、full instance2/gen0未变。403日自然月检在同一 Native448/date53154000 暂停帧先完成 completion 和 opinion，两者均 available；随后 termination 仍以 `sway_termination_executor_unavailable` 失败，整体 query_failed 未被改成成功。AUTO551 继续实际 life-advance，外层无错误，但没有 `sway_following_turn`。该小摘要不含403日具体意见数值，不能从稍后 ledger 倒填。

07:28:28.941947Z 冻结的正确 `runtime/state` ledger 中，completion 和 material 同为 Native825/date53160816（第687日）。总意见为18，旧第61日为17，证明 material 的数值及来源确实刷新；两个 Sway 专属 modifier 都已观察且 absent，具名增量为false，first_named_gain不存在。总意见增加1没有归因给 Sway。原计谋仍 active/continue，Start receipt 和 capture 原件保持原样。

material 保留的 consumed=true/following Native583/date53156400 来自第503日，早于687日刷新；不能据此给当前刷新、具名收益或终态新增消费信用。M6仍 in_progress，不提升为7/8。最初把 Sway 查在 `state/native-session` 的 wrong-scope冻结原件保留，其absence不能当作计谋消失。

本包没有新RPC、提前月检、Start/Stop、活ledger/Driver/SAVE读取、编译、部署、源码修改或重复测试。部署修复的实际成本明确：原先因termination短路的自然月检，现在会执行一次已有配置的必要opinion查询；没有新增endpoint或每AUTO cadence。小记录沿原研究预算，未来预留0，既有来源保护期不延长；派生记录于2026-10-21复核。
