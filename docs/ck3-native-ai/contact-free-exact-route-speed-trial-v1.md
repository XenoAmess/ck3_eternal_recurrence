# Contact-free typed route：一次独立speed5试用

该后继只改变已有fresh `contact_free` typed exact-route一天的墙钟速度；目标仍`start+24`，沿原exact clock，原Army路线与完整同帧isolation证明、事件、模态、暂停、月界/终点及Arm/Status校验不变。默认关闭；全局route speed/effective speed仍3，global high-speed A/B仍false。它不授route-window、committed-route、hold或active-battle任何新速度资格，不能替代这些路径的Army watch。

`machine_id: xenoamess-full-tower-eb9d2c1186`；身份及源hash读回`2026-10-19T08:24:26.282248Z`，来源`tools.ck3_live_run_id.current_machine_id()`。本次只有软件Driver→Protocol测试，没有更改C7/现场或进行Native/Game/RPC/SAVE读写。状态为**SOFTWARE_DIRECTED_PASS / CONTROLLED_TRIAL_PENDING_LIVE**；实际吞吐收益unknown。[前置源审](typed-route-exact-speed-five-source-review-2026-10-19.md)保留原C7/Native26身份及speed3事实，[小回执](evidence/contact-free-exact-route-speed-trial-2026-10-19.json)绑定本次候选。

唯一显式入口是`NativeHeadlessGameplayDriver.configure_contact_free_exact_route_speed_trial_v1`，在既有构造和campaign cadence配置后调用，例如未来受控冻结入口：

```python
driver.configure_campaign_score_cadence_v1(
    campaign_id="robert-first30-v20261019", start_date="1066.9.15",
    start_date_raw=53144328,
)
trial = driver.configure_contact_free_exact_route_speed_trial_v1(
    campaign_id="robert-first30-v20261019",
    trial_id="contact-free-route5-controlled01",
    speed=5,
)
```

上例是未来入口recipe，**本次未安装**。方法不读现场、不发RPC，不改变构造的global AB。必须匹配已配置campaign，显式speed只允许int5；配置身份不可更换。返回`qualification_status=controlled_trial_pending_live/live_ready=False`，不能从调用成功宣称实机已qualified。未配置driver保持旧回包语义，无新增trial字段。

当前fresh proof验证仍先执行。只有contact_free、paused map、无已知玩家决策，并且真实capabilities同时含route-query、Arm/Status/Cancel、speed5/resume/pause，才选择5；缺项保持原3并在结果标原因。不可避免接触仍1。专用配置强制global3/ABfalse，不能借全局AB或某个其它scope readiness进入本试用。

**一个driver最多选择一次route5尝试**。次数在提交setter/Arm/resume前消耗；结果未知或失败也不自动重试。重复同一configure不能重置次数，换trial identity被拒绝。以后自然route继续原3，仍使用新帧、新proof和原时钟；不需要人为停游戏。终点已到不消耗试用、不resume。配置只在该driver内存中存在，后继普通维护重新创建driver时必须明确选择是否配置。

结果附`contact_free_exact_route_speed_trial_v1`，记录campaign/trial、`selection_status`、attempt limit/used/ordinal、原source snapshot/public/native revision/date/episode/generation、subject/target/完整hostile IDs、selected/actual speed和原actual elapsed/progress。`native_army_watch_claimed=False`、`live_ready=False`、`calendar_or_business_credit_inferred=False`固定保留；实际日信用仍由原Native clock及外层前后MET授予。这个exact clock是`terminal-a0`，不能把完整route proof包装成Native Army watch。

必要验证已完成：8个新增定向node通过，包含真实query→原fresh proof→原exact clock的3/5同输入对照，命令生命周期与关键日期/war/event/paused结果一致；第二个自然新帧route退3且重复配置不重置；原陈旧帧/危险sibling拒绝；错setter/Arm速度与过冲拒绝且试用已消耗；零日模态按原generation cancel、不冒充一天；一天普通事件保留；月界、30年终点0resume；缺Cancel能力不试5。另3个既有global AB/scope隔离/五速selector node通过。无全矩阵或原生重build。

未来有限实证只需以下顺序，不为benchmark制造军令、重走旧route或回滚存档：

1. 下一次已经需要的SDK维护使用Root冻结的新source tuple，在构造global3/ABfalse、同campaign cadence后只配置该入口一次，保留配置回执。Native26身份与现有capabilities沿原启动读回，不另取重复样本。本recipe不要求现在暂停/重启C7。
2. 等普通完整规划器自然选择一个eligible typed contact_free route。已有route查询必须绑定当前全部敌军、路线与isolation；无法符合时继续原3或其它原流程，不硬触发试用。第一次5最多一次，后续自动回3。
3. 从原closed AUTO及原前后MET保存：源/配置身份、fresh proof绑定、真实speed5、same Arm generation、target=start+24、ticks1、overshoot0、实际paused、一次resume；现有原件还应保有当前Army路线/位置与事件材料。只授这次实际clock与对应source tuple，不把ACK当到达/战果。零日modal/event或未知失败保留实际日期、ACK及cancel诊断，不重复原动作，不填成一天。
4. 核后继新proof使用新帧且恢复speed3；若自然到达/接触/事件素材尚缺，对应变体仍unknown。仅在得到这些自然素材后讨论扩大有限次数或生产默认，不自动翻转readiness。墙钟用完整闭合批含查询、规划、日志等除以实际日；同输入软件对照不能授吞吐目标。

当前可实施成本为一个纯配置/receipt叶、driver13行接缝、一个定向测试文件，无每AUTO新增RPC。旧C7 FULL1213 clock主体12.8519秒/12日值得研究；即使全部去掉，该片段其它工作仍1.41786秒/日，不能宣称仅route5已满足1秒/日。

记录按通用storage `record`类别，复核`2027-04-17T08:24:26Z`；本包新增文本小于64KiB，没有大产物。
