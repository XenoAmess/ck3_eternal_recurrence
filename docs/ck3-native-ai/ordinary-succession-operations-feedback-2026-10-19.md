# 继承运营：逐头衔反馈与同一公开帧内的失效缺口

`machine_id: xenoamess-full-tower-eb9d2c1186`。实际源码观察 `2026-10-19T04:27:58Z`—`04:41:00Z`；[机读证据](evidence/ordinary-succession-operations-feedback-2026-10-19.json)固定来源和软件结果。没有操作当前 Game、Native、MCP 或桌面，没有读取活 Driver、SAVE、媒体或新局回执。Root 授权后只改 Driver 的继承失效 API 与 Service 的新 root 完成接缝；war/strategy 与 M4 Crown 分支未改，也没有重验已完成 M3 的旧业务合同。

目前完整普通 planner 的确会刷新完整 expectation，但“能对账继承”与“能提前经营继承”之间还缺消费链。`ordinary_campaign_goal_plan_v1` 固定 `focus=marriage`，婚姻优先级100、继承/分割 review60只是文本；没有读取实际逐 title 分配。已有 player-vitals 产 succession preparation 信号，现有普通风险 context 仍是事实投影，未发现以此选择可执行继承治理动作的链。支持的 Crown 法动作只到既有 CA0→1、CA1→2；不能因为其合法就当作分割改善，也不能凭未知收益增加威望及政治支出。本轮不修改原 Crown 政策，不新增其继承偏置。

## 真正需要补的 freshness 接缝

`Service._prepare_succession_transition_v1` 比较 snapshot ID/public revision/Native revision/date。不同则沿原 root/turn-bundle 路径冻结 living 前代的完整 title rows；相同则保留期待。事件/通知先走其原处理，不强迫当场重读继承；死亡终态沿原 reconciliation。日期推进与公开帧变化能使这一路刷新，但公开帧不是 estate/law epoch。

实际 Native `game_contract.hpp:2279` 的 `Snapshot` 列出日期、速度、暂停、玩家身份、钱包、配偶、事件/通知、战争、军队和 settlement；**没有** held titles、primary title、继承向量或 active laws。默认 `operator==` 只比较这些字段。`bridge.cpp:12660` 的 `PublishSnapshot` 在 Snapshot、checkpoint sequence、modal hint 均相同时 deduplicate，`12669` 才递增 revision。因此不能证明每一次同日头衔、法律或非玩家候选人变化都会改变上述四元。旧 root 与新 root 可以具有相同公开四元、不同实际 estate；只按四元保留 expectation 会漏掉这类变化。

本轮新增 [纯失效叶](../../ck3_autonomous_player/src/xar_autoplayer/bridge/succession_expectation_invalidation_v1.py)。它消费**已经完成且经过原 owner 校验的新完整 campaign-root result**，复用原 `build_turn_bundle_v1`、完整 freeze 与 expectation normalizer，对比全部 title rows、primary ID 与 primary first heir。发生差异时返回 detached state 的 `expectation=None/reconciliation=None`、`refresh_required=True`；不改原输入，不直接采纳新预测，不操作 Driver、不做 RPC、不授权动作。unchanged 则保留原 state；旧 actor/episode、混合帧、terminal 或不完整 estate 不能清状态。

纯失效 compound 使用原生产 Service/root materializer 的合成输入，保持公开四元不变，分别改变其他 title 的 first heir、移除 held title、替换 primary ID、改变 primary heir。四例都清除两项旧派生值；同 estate 不清；混合 Native revision 与终态拒绝，原输入及调用计数不变。

实际源码已接入 `GameplayBridgeService.query_campaign_root_context_v1`：只有原 `execute_step` 真正完成新 root 才置标志，结尾通过原 envelope/normalizer/build、独立同帧后验并构造带原 `binding` 的 response 后，调用 Driver API。`_planning_root_result` 旧缓存复用不触发，避免旧 cached root 反向作废更新的期待。公共 response 形状未改。

Driver 在原 retain 方法前新增 `invalidate_succession_expectation_from_root_v1`。沿原 `_driver_state_lock` 先后核当前缓存 publication、episode 与 detached 输入仍精确相同，只有完整 estate/primary/heir 实际改变才清两字段、置 dirty，退出锁后调用原持久化路径。未变零写，竞态 frame 拒绝且保留原 pair；terminal/非 living/不完整 root 保留前代预测给原自然继承对账。复用 Service 已独立读回的 snapshot，锁内只读现有 protocol semantic cache，不增加 full observer 或 Native 查询，避免把可持久化的 observer 放进 state lock 而倒置原锁序。持久化只记录调用尝试，不声称新增 durable/fsync 保证。

下一次原 `_prepare` 见到 `expectation=None`，沿已有路径处理；定向实际 Driver+Service 源码接缝测试证明能复用 history 中刚完成的新 root 重新 retain，额外 root 调用为零。接缝 compound 也覆盖 fresh unchanged、旧 cache 不调用失效 API、同公开帧实际 heir 变化、frame 竞态和 terminal 保留。这里的“实际”指生产类方法与 Service 的软件接缝，不指当前游戏部署或业务通过。

覆盖范围仍是 **Service 实际新 root**。部分私有 family 等入口直接调用 Native driver 的 `_execute_campaign_root_context_v1_query`，绕开 Service，本轮未覆盖。Native driver response 还没有 Service 的 `binding` rendering，不得拿当前 snapshot 倒造缺失来源；后继可复用它实际 `queried_*` 字段与当前原校验结果形成原 bundle 输入。

尚未观测到新 root、且继承相关变化未进入公开 Snapshot 时，仍没有专用 estate/law epoch。本叶不能识别未被查询到的变化；不通过泛化所有事件、额外每 AUTO RPC、降低观察频率或让旧预测失去真实性来掩盖它。已确认会改变相关输入的合法动作回执可后继绑定针对性失效，但当前没有把一般事件、任意 Crown ACK 或未知结果当作此类证据。

## 将具体风险交给长期 planner

新增 [纯运营事实叶](../../ck3_autonomous_player/src/xar_autoplayer/ordinary_succession_operating_context_v1.py)，只消费完整 retained expectation，严格核 living/paused/map/actor/episode 与六字段；活动事件/通知优先 deferred，旧或不完整预测 typed unavailable。它列出 primary-title heir、每一项分配、分给其他 heir 的个人 estate、无 observed heir 的 title、分给其他 heir 的同级或更高 title，以及两个可比完整预测间新增/移除 title、first-heir/primary 变化。

不同 heir 分到县，证明个人 estate 分割；它不自动证明县离开 realm。同级 title 分割是需进一步审查的风险，也不自动证明将来独立。primary-title heir 不单独证明当前合法 player heir、其 dynasty 或未来存活。本叶明确列出这些缺口以及实际法律、合法动作成本/政治后果、原生 counterfactual 等缺失输入。它不列 Crown 或其他动作候选、不改变原优先级、不作查询。公开帧相同也明确保留 estate/law epoch 未闭合的范围。

本事实叶仍是 **source-only，未接入普通 planner 消费**。后继可把此 context 附到 `Service` 已建立的 `campaign_goal_plan`/实际 decision 理由中，使继承风险具有 title ID 和来源。动作仍须走已有普通 planner 的原合法通道；没有实际可行、值得做且能改善该风险的动作时，保持事实缺口并继续完整普通游玩。要新增变法、指定继承人、剥夺继承权或分封优化，必须先取得 exact-build 同源合法性、费用/政治代价和效果证据，不能把 read-only law profile 当 mutation capability。

最终定向验证 **3 passed，2.39秒，外层0**（chunk `41fa5c`）：两项纯事实/失效 compound 加一项生产 Driver+Service 接缝。早期 primary-ID 合成变更未按原 native canonical title 顺序排序；首次 cache 夹具误放 Service-rendered result 而非原 Driver root。两次都只修复夹具，原 normalizer/缓存校验未改。没有当前局运营提升、自然继承、已部署 freshness 修复或 G2 增项信用；M3 原 complete 与 G2 6/8 保持。新增小源码/测试/记录远低于1MiB，无重型写入与删除。紧凑记录复核点为 `2027-04-17T04:41:00Z`；实际 root/source tuple 的后继采用由 Root 与唯一 runtime owner 另记。
