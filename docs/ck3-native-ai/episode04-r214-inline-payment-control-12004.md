# R214：既有付款内联采样的真实边界

机器 `desktop-3fevhd2-1c74096080`；研究源 `191568c281bbde92feeb9f96fe40736be1b63ca8`；a36 原生源 `7a342116d8aaa8a4c645941199c3ef1abd0a7c8f`。本件仅离线源码核查；没有 SDK、现场、DR、构建、旧矩阵或主树修改。本文不授本场采样开启或付款正例。

`ck3_query_war_cash_current_resources_private_v1` 的 `payment_sampling="enable"` **只开启 a36 DLL 内已经安装的 WarPaymentJournal 记录门**。DLL 初始化时在主线程已暂停的既有注入阶段安装 entry detour，安装后采样初始 OFF。现金查询的 enable 分支只调用 `ControlWarPaymentWindow12004` → `journal.SetEnabled(true)`；它不再次安装 hook、不启动进程、不调用 DebugActiveProcess 或设置线程硬件断点。generic context 中的 `RtlCaptureStackBackTrace` 是本进程有界栈采集，不是外部 DR。旧 external writer observer 是另一条路径，不必为了开启此 journal 而运行它。

a36 的小型生产资格记录中，现金私有查询、WAR_PAYMENT_PASSIVE、GENERIC_CONTEXT、RAW4_GETTER 和 NATURAL_PHASE 五个 flag 均为 ON。该静态资格不替代本场实际 `installed` 与控制读回。公共 host 还必须已用 `host_features.war_cash_queries=true` 映射到 `--private-war-cash-queries`；不得给运行中的旧 host 热注册。

这是有副作用的研究采样控制，不应把显式 enable 称为纯只读。它不发送游戏付款、任命、移动或时间推进动作。省略两个可选参数走默认读取，不会打开采样；显式 `query` 也不打开采样。

启用须满足实际 paused/map-ready/alive 玩家帧、exact .4、非零 connection generation/native revision，且 natural_phase 已安装、available、capture_enabled、非 busy。它读取当前进程 PID/FILETIME、实际 GameState 指针及原生日期，绑定玩家 FullID、机器和 journal epoch。成功须独立保全原 response 中：

- `war_payment_control_v1.accepted=true`，reason 为 `enabled_controlled_no_load_window` 或 `already_enabled`；
- `war_payment_observations_v1.installed=true`、`install_failure_flags=0`、`controlled_window_admitted=true`；
- `sampling.available=true`、`capture_enabled=true`、`epoch>0`，并与当前真实 session/frame 一致。

生产 Python normalizer 会验证这些字段。一次未知控制结果不能重投 enable。已 admitted 时同身份的重复 enable 返回 already_enabled，不建立新证据窗口；不应把它当清空后新 epoch。

窗口合同明确是同 owned process 且无 Save/load。`loaded_game_epoch` 刻意为 null，GameState 指针、journal epoch 或进程时间不能冒充加载 epoch。native 可因 natural_phase OFF、GameState 改变/读失败、日期回退、玩家/连接变化关闭窗口；它没有证明能识别同地址的所有加载。因此查询和保存的正确顺序是：**先保全付款 query 原件，显式 payment disable 并验证 clear，再 all OFF/clear，最后 Save**。暂停/恢复本身不会使身份失效。关闭或失效会清 journal，cleanup 后计数不能代替关闭前证据。

实际可消费字段在 `war_payment_observations_v1`：`current_session`、`sampling`、`records`、`natural_parent_returns`、`natural_journal_status`、`qualified_boarding_debits`，以及编译开启时的 `raw_resource4_getter_v1`。严格扣款包含 payer_character_id、requested_amount_raw、entry/return 余额及 writer/transition/gateway 三个 sequence。生产 Python 从完整 raw parents、同 session/thread/order、自然 post-date 返回和真实余额 SUB 重新计算，要求 native claims 与之完全一致；512/64 环溢出或 publication failure 会失去该严格扣款资格。

这个严格列表只接受已知登船链：transition return `2A9A8C5`、gateway return `24E8F40`、personal SUB `28B99B2` 或 land SUB `28B9A6D`。`kind=2` personal ADD 不属于该列表。generic NET 回调可保留 context `+2C0/+2C8/+28/+30`、公式输入、钱包原回调 entry/return 和 unwind parent；但 native 与 Python 都将 `maintenance_attribution` 固定为 `unclosed`。因此该 journal 有机会直接提供已知登船 paid/payer，不能仅凭相同值、personal ADD 或当前军费向量关闭维护军费 paid/payer/cadence。c/d 实际 writer PC → 同次 NET 因果仍未被内联叶观测；普通 external=false 不允许为了该剩余问题运行外部四槽 watch。

本场唯一 core 日的参与卡见 `REQUESTS.json`。当前冻结 R214 executor 不能原样外部先 enable 再运行：core_day 76–77 只允许 regular_core ON，其余必须 OFF；Session.sampling 116 又把 regular_core_full_carmy_ids 附给每个 enabled=True。Root 若明确选择并行内联观测，须由同一 actor owner 新建薄变体：scope 参数仅对 regular_core 添加，允许 ON 集合恰为 regular_core+natural_phase，并在同一次 exact_day 前后接三次现金控制。旧 actor 原件保持；本件没有修改它，也没有新增第二 clock。

一自然日或月界不是已证维护结算机会。空 journal 不证 fee=0、无 payer 或否定 cadence。视频可说“本次开启既有内联采样并保留实际钱包回调证据”（仅执行后），不能预说“已支付军费”或“每月一日结算”。

来源片段、Git blob 身份、a36 生产小回执 pin 与既有生产 consumer 入口见 `SOURCE-FACTS.json`。未读取 R213/R214 大 raw、未生成整映像或额外原片副本。
