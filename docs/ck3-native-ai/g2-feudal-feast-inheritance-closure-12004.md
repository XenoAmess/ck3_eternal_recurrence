# 干净1066罗贝尔：宴会与合法继承的最短剩余闭环

2026-10-17；机器 xenoamess-full-tower-eb9d2c1186。只读SDK37 CLEAN03、原版1.20.0.4文本与既有专题，不访问Game、管道、现场、Driver、SAVE、视频或当前队列；不改W、SDK或准入。Root通报新Game230672/SDK37已运行，但本包没有独立观察其业务状态，旧局天数、战果和继承次数均不带入新局。M0–M7仍6/8，M6/M7仍in_progress。

## M6：已有经济准入，剩下一场真实完整宴会

| 已有链 | SDK37源码位置 | 可复用事实与边界 |
| --- | --- | --- |
| 完整普通planner接入 | xar_autoplayer/bridge/service.py:2766–2871 | 仅原计划选择life-advance后仲裁新宴会；pending先观察原意图、不再Start；未满足条件保留普通推进。不是独立非战规划器。 |
| 原版配置与合法性 | activity_feast_ordinary_v1.py:8–54 | 当前首都候选经原版Open、Stage1 generic确认、Stage2 CanSelect与目的地选择到Stage5；配置成功明确no_activity_started。当前Native能力/配置必须由实际运行自己的既有输入证明，本包不由source推定已启用。 |
| 经济和承诺 | activity_feast_stage5_budget_v1.py:21–114；activity_feast_stage5_value_policy.py:17–132 | 同paused/map/actor/public/native/date/snapshot绑定；gold/treasury/piety/barter_goods四项实际quote/可用余额；未决建设、gift、婚配或interaction不当零承诺。200gold独立现金底线；战时实际最大月maintenance×18只是可支配支出分配，不是战争成本上界。未知不得当零。 |
| 参与者准入 | bridge/activity_feast_stage5_start_private_transport.py:403–490；activity_feast_stage5_start_formal_consumer.py:56–137 | 已有原生规则成员、正join权重、travel_days、arrival≤planned_start与same-frame；普通候选可满足现有入口，不需要为了验收人为指定旧guest ID。 |
| once-only开始与物质结果 | activity_feast_stage5_start_formal_consumer.py:143–179、525–584 | 先持久化pending，再一次Start；ACK后等待发布、独立post核对新full Activity与精确支出。未知提交保留原意图，不凭ACK授成功或盲重发。 |
| 终态与结果消费 | bridge/activity_feast_terminal_outcome_v1.py:21–118；formal_consumer.py:248–348、421–469、587–604；Service:2019、4694–4700 | exact full Activity/instance-generation/host/type匹配的current native flags或retained cut；absence保持unknown，readable ongoing不由旧记录覆盖。下一日期的following消费不等于宴会已结束。 |

参与者风险没有被现有join/arrival门禁解决。原版feast.txt:746–759规定成人、健康、外交范围，同时允许普通host/guest的murder_attendee意图；选择feast_type_generic仅避免主动选择独立murder-feast类型，不保证无人行凶。原版is_valid:46–57要求活动阶段有实际attendees；:147–155无人到场会走invalidated。因此正join权重、曾经opinion62或已邀请不能当出席/存活结果。

原版feast.txt:4992–5015把普通host的completion引向feast.7101和disburse_feast_activity_rewards；:5113–5130对存活、未囚禁的非host参与者分支发放Reveler并调用健康/体重效果。00_activity_effects.txt:3746–3751对host普通收益也调用这些效果。pam_effects.txt:1559–1580仅当personal-tenet flag、体重阈值、可患gout条件同时成立才进入75/25权重分支，不能推成当前Robert有25%风险或无风险；PAM是原版文件，并非按前缀认定mod。现有guest opinion/modifier reader可读具名关系结果，未提供校准的参与者死亡/谋杀/旅途风险效用模型。本包不把新风险模型增加为当前开席或游戏继续的门禁。

最短自然闭环只需同一场：

1. 普通完整plan自然选中generic Feast时保留其已有Stage5 inputs、实际quote/余额、budget与guest-route来源；不强开、不套用旧100gold或旧guest身份。
2. 一次Start及独立post，绑定本局actor、full Activity、真实debit、原意图和post frame。配置/ACK不足以算Started；unknown仅沿已有reconcile处理。
3. 自动游玩继续处理当前实际MCP可用选项。未知选项仍记录后选任意可用项，异步学习；事件source-known或通知关闭不等于活动完成。
4. 既有hosted-post/retained-terminal链读出真正completed/invalidated/两者及其来源；独立post-terminal prestige/stress/Reveler读回。formal_consumer:279–346及:181–244故意保留benefit_verified=false、attributed=false，故整段数值差或原callee区间也不能直接宣传“宴会净收益”。若需要具名opinion收益，复用已有guest-opinion/modifier读回且证明该guest实际参加，不新增getter。
5. 已有普通following/下一完整plan及正常存档保留同一receipt。后续若原流程自然cold，再对比原full Activity/ledger/结果；不为本研究专门停机或重复Start。

旧Robert29829和Murchad已有Start、100gold debit、ongoing与事件收益的历史实证可证明部分实现曾工作，不能填本局终态/出席/收益，也不能仅靠一场宴会宣告M6完整：有用scheme真实Start→terminal→独立结果仍属于M6剩余资格。

## M7：复用已合法的普通继承链，补本局自然证据

SDK37 bridge/succession_transition_contract.py:140–228已支持纯原版新局：显式fresh no-pact、已知空profile和Root实际启动日志证明，经原字节pin校验产生xar_enabled=None/pact=absent_by_verified_xar_mod_not_loaded。该合法合同不同于历史xar_off；本包不再加旧XAR规则，也不把缺字段当未加载。公共tools/g2_saved_campaign/m7_ordinary_successor_queue.py:17–37已有同一严格predicate。该资格的实际本局生产者与部署事实归Root，不由本报告回填。

最短自然路径为：

1. 活着时沿现有Service._prepare_succession_transition_v1保留原生primary heir与每一held title第一继承人、actual binding和campaign_goal。分封风险split_successors不是失败或可手改状态。
2. 真正played_character_changed后，Service:1421–1447取得同帧真实后继turn bundle；succession_transition_contract.py:581–704核对实际played successor及前代有限estate。期待由别的heir取得的titles不要求继承人夺回；其先前已有额外titles只列信息。未匹配不伪造“合法对账成功”。
3. NativeDriver:22820–22925仅在paused/map、alive已played successor、same-frame matched successor/title结果下执行continue-as-reconciled-successor；这是episode/goal重绑定，不是再次触发死亡或更换游戏统治者。它沿既有family episode handoff存档前代结果，清旧战术候选，以新统治者真实关系和军队重新规划。
4. 保全已完成Continue的原回执，消费completed分支不重发。已清death surface直接走普通计划；真实death modal才用既有typed Close。必须选择的event/interaction保留并沿正常MCP选择，不拿强行SAVE越过它；既有async owner可延期checkpoint，不能因通知误授继承成功。
5. 下一完整普通plan的campaign_goal_plan_used应保持campaign_id/goal_key/origin，current为真实后继、progress仅增已核对transition；之后正常季度SAVE保留一致意图。本任务不增加额外存档频率。后续自然cold只复用既有恢复与离线tools/extract_g2_goal_continuity.py、extract_g2_owner_cold_evidence.py投影，不新建恢复器或为补研究重启。

与宴会交叉的真实剩余边界：feast.txt:60–79的host-death只写guest feast.5003与heir feast.0800通知，不能从中断言引擎绝不会换host，也不能断言继承人继承宴会。SDK37 formal_consumer:445–451对原host与现actor不一致返回lifecycle_other_actor_or_frame、terminal=false，且在新的hosted query之前；它不会替旧host伪造terminal或新Start。旧Activity原结果继续保留，后继按新身份规划；若未来这一路实际缺旧host终态，仅记录那个局部未知并交离线处理，不把heir单按钮通知当旧宴会成功、收益或M7继承信用。详见已交p37-g2-m6-feast-host-death-static01。

历史31254→40526已有SAVE13、物理cold来源、后继normal plan消费同一dynasty_continuity的闭场证据，证明这条复用路线不是新造接口；它不记入Game230672。新局自然继承及之后正常规划/保存尚待本局实际回执。更广seed/government玩法资格仍缺，此次只收口自然feudal机会，不为矩阵另开游戏。连续30年无停机修复由主稳定ledger计量，不可代替M7 intent或更广身份资格。

## 移交和校验

来源具体SHA、行段与静态绑定校验见SOURCE-AUDIT.json；SDK37manifest为ef5a2dac99fa2a518c9c5218c33094117002b8c7d2be0dff69474fc631fb45b7、1319叶。本包没有源码修改候选：上述最短正常链已存在，当前缺本局真实结果，不是再补通用接口。只执行一次静态source/pin校验，不重跑旧矩阵、不调用SDK或仿造实机fixture。sole Git writer可收此文与小型audit，不复制源码树、运行端或历史大件。所有数字/路径均保留时效；DELIVERY与storage receipt另附。本报告不授M6/M7、稳定天数、性能或新局业务完成。
