# M6 新局首次真实普通 Sway Start

`machine_id: xenoamess-full-tower-eb9d2c1186`，`robert-first30-v20261019`。
本包于 `2026-10-19T03:33:09Z`–`03:34:34Z` 离线读取 runtime owner 明示的已结束 AUTO48/50。
[自然观察小回执](evidence/g2-m6-first-natural-start-2026-10-19.json)与
[tuple 来源记录](evidence/g2-m6-runtime-adoption-2026-10-19.json)分开保存。
G2 仍 **6/8**，M6 保持 `in_progress`。

## 已发生的窄业务事实

AUTO48 于 `03:27:59.168924Z` 返回普通 `ordinary-sway-opportunity-v1`，真实 Start 的原身份是：
actor `31254`、target `33946`、action `sway-88765ff2258b45f88acb5eeabc1f63c2`、full SchemeID `2`、generation `0`。
原 native receipt 为 applied；独立 active read 保留同 fullID/gen/target、progress `0/353`。
receipt capture `421034` 后，独立 capture `421038`；两者日期均为 `53144328`，Native revision `8`。
公共严格 Start classifier 对该原回执纯离线运行一次通过，只授 `sway_start_applied_primitive`。
这次真实 generation 0 已进入 post-Start observer，不再被旧正整数代次检查误拒。

AUTO50 于 `03:28:02.368170Z` 实际执行原普通 `life-advance`，日期 `53144328→53144520`，推进 8 日。
其 `sway_following_turn` 保留同一原 Start，`next_turn_consumed=true`、following Native revision `18`。
此处只能证明 Start 和已有 active 实例观察被后来普通回合消费；没有具名收益，也没有终态消费。
`terminal_intervention` 这次实际仍为 `tracked_instance_active=true`、`instance_terminal_outcome_observed=false`、
`native_status_key=continue`，不能被字段名称误导为发生终局。

## 首次真实命名基线缺口

AUTO48 post-Start 的 completion 已 available 并确认原实例 active。
紧接的 `query-sway-completion-termination-v1-private` 返回 `unsupported native gameplay step`，
现 observer 在此 break，opinion 实际 `requested=false`、`not_requested`。
因此没有生成早期命名 baseline、`material_intervention` 或 `first_named_gain_intervention`。
原 optional 回执诚实保留 `outcome=unavailable`，同帧为 true，零重试，下一观察期限 `53145048`（原日期后 30 日）。

这不是未遇合法机会或缺 flags，也不是收益丢失；这是已开启 reader 与当前 Native25 支持范围不符，
使后续独立命名 reader 没获得调用机会。原 Start 已完成，不能为补基线重发。
已向 Root/runtime owner 报告：在本来必要的 SDK-only 维护中，优先关闭这条已实证 unsupported 的
termination-query 权限，保留原 completion/opinion 通道及其它失败守卫；实际意见读取能否成功仍需以后正常观察。
本包没有修改权限、源码或现场，也不补造未请求的基线。

`03:39:19.577677Z` 追加精确路由核对：Python `STEP` 与 C++
`kSwayCompletionTerminationStepV1` 都是 `query-sway-completion-termination-v1-private`，并无可用的 Python 改名接缝。
Native25 的 7025 B `SOURCE-FREEZE.json` 把当前 DLL 绑定到 Native24 的 `nonwar12002.obj`；
其实际编译回执记录 source SHA `ed55cf48…30feff`，本次实读冻结源及当前公共源均符合该 SHA、52606 B。
该源 `IsNonwarPrivateStep12004` 的 483–496 行只允许 completion/target/formal/stop/opinion，
没有 termination；旧 `.2/.3` gate 的 638 行和共用 handler 的 779 行则存在。
实际冻结 `bridge.cpp` 在 15548 行先检查该 exact `.4` gate，未命中后才返回本次 unsupported。

因此准确分类是 **Native exact `.4` dispatch 不可达**，并非 Python 名字错误，也不是物理 provider 完全不存在。
原 Native25 link map 明列 `.4` installer、termination handler、mailbox executor 与 serializer，
但符号存在仍不证明一次真实 provider 查询成功。当前 SDK-only 关闭这条不可达权限属于真实能力绑定；
completion/opinion 继续使用原通道和 fail-fast，下一次普通到期读取再记录实际 baseline。

后继 Native 施工入口为
`ck3_autonomous_player/native_bridge/src/ck3_12002_nonwar_router.cpp::IsNonwarPrivateStep12004`：
在既有 active-scheme 宏下明确加入唯一 `kSwayCompletionTerminationStepV1`，
沿已存在的 handler、process-lifetime recorder、owner executor 和 serializer 闭包复核，
下一次必要 Native 合批重编该对象并重链。定向资格应检查 exact `.4` gate、原 step/参数/完整实例、
typed unavailable/空 ring 的真实语义及独立同帧输出；不制造 terminal、不借此放开其它尚未核闭的 route。
本包只记录入口，没有改 Native、编译、加载或新增现场查询。

## 仅一次被动收集

[显式 manifest](evidence/g2-m6-first-start-manifest-2026-10-19.json)只含 owner 已结算的 AUTO48/50，
大小分别 `87990` 和 `99076` B，SHA 在本包独立读回一致。
现 [collector](../../tools/g2_saved_campaign/m6_closed_evidence_collector_v1.py)只运行一次，
产生[原始指针索引](evidence/g2-m6-first-start-pointer-index-2026-10-19.json)，1 个原实例组，0 RPC。
索引明确不授 M6，也不独立判断完整资格；本次没有重跑旧测试。

tuple 元数据复核有一项范围偏差：`ROOT-FINAL-SDK-FREEZE-P37.json` 实际为 `399506` B，
被完整读取一次后才发现超过预期小元数据大小，1423 项文件表输出被截断。
本包不再重读该表，只记录它的精确 pin 和必要顶层字段；collector 真实输入始终只有两份小 AUTO。
没有读活跃 ledger、Driver、SAVE 或媒体，没有新增游戏/RPC/Start/Stop，也未操作当时的 publisher halt。
全部新增物仍为小文档/JSON，沿 Root 统一存储预算和 48 小时派生复核，不新增容量信用或删除。
