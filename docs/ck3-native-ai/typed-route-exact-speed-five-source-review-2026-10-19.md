# Typed route exact-day speed5：独立后继路径的只读源审

结论：Native26已有合法speed5的同一每日截止通道，源码不需要新增DLL；C7的typed route使用speed3是Python资格/配置限制。可以做仅限`contact_free`、仍每次推进1日的后继组合，但当前没有独立route5实机资格，不能直接启用全局A/B或借用generic speed5、committed-route、objective-hold、active-battle资格。本次没有更改速度、源码或现场，也没有新测试、构建、RPC、Driver/SAVE读取或媒体。

`machine_id: xenoamess-full-tower-eb9d2c1186`；本次开始读回`2026-10-19T07:53:15.275833Z`，身份来源为`tools.ck3_live_run_id.current_machine_id()`。以下机器事实只绑定此机器。原c0338历史编译回执无机器ID，仍为`machine_id: unknown`，不补猜编译机器。小型record，复核期限`2027-04-17T07:53:15Z`；Root负责本轮统一容量检查，本叶无重型写入。

## 固定输入与现状

- 实际C7源码根`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src06`，business `8e1e59f073f239d266f5b59f57c65b5645658512`。实际`bridge/native_driver.py` SHA256 `f64d8c6478b37fe39a3baca6f7794b89a1e20072b443895b9e9e29de6158226f`，没有用dirty master代表现场。
- [已封战时源审](evidence/g2-m0-c7-war-route-convergence-2026-10-19.json)绑定FULL1213 compact `fc3e3eeccd51de35650c4adb9a53a1551b01d7d3db3ca79e6d507467c9c958bb`、trace `e3777c3db721e47dd25bf491eef74178d49acc34c61e458aec9107241b18ca88`。该30周期片段12次route advance各+24raw，共12日；不是重复move，也没有证明可删除的同帧重复查询。该既有证据代替扩读现场原件。
- Native26固定根`D:/codex-ck3-demos/2026-10-19-robert-v20261019-native26-performance01`。`QUALIFICATION.json` 6248B/SHA256 `5d0f0fa3d97642e18dba3c247d55ca87c43ee2c5b1031de0a80d0702e3f0ce03`；DLL18442752B/SHA256 `eaee4443f083ae5055232b908fdb5c6555aa75084801fd24654224b090032184`，本审计未重hash DLL。[构建记录](evidence/native26-performance-build-qualification-2026-10-19.json)保留当时未部署事实；当前采用身份由runtime既有C7冻结绑定提供，不拿构建成功代替route5实机通过。

## 为什么当前是3

下表行号均指实际src06的`bridge/native_driver.py`。

| 接缝 | 实际合同 |
| --- | --- |
| 793、1958–1995 | 默认`DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED=3`；4/5要求显式全局A/B或已授scope资格。`route_contact_effective_timeline_speed`专门防止committed/hold资格流入exact route-contact。 |
| 23983–24020 | `_execute_route_contact_horizon_advance`重读当前semantic帧、核expected revision及fresh proof。只有`proof_kind=contact_free`读取effective speed；不可避免当前省接触强制1。随后调用原`_execute_life_advance(exact_one_day=True, preferred_speed=...)`。 |
| 30180–30307 | `_exact_route_contact_timeline_policy`已表达1–5；只消费已验证preference。unknown、不可避免接触、battle identity materialization仍1，缺指定setter能力退1。 |
| 25042–25063 | generic exact-day/reader-unavailable独立speed5分支只接受`result_step='life-advance-one-day'`，不会授typed route步骤speed5。 |
| 24235–24303、24401–24418 | route-window取effective speed；committed/hold取typed step速度并核scope资格；active-battle decision明确3，terminal cruise可5但另受原策略资格。`_BATTLE_SPEED_READINESS`中committed/hold4/5和overwhelming matrix仍false。不能扩大本次目标到这些scope。 |

旧`--route-contact-speed 5 --allow-route-contact-high-speed-ab`会同时影响route-contact/window和其他配置消费者；它是既存实验入口，不能冒充独立exact-route5资格。现有`test_mcp_route_contact_speed_config.py`及`test_native_bridge_driver.py::test_exact_contact_selector_represents_all_five_speed_arms`只说明参数/选择器可表达，不证明C7实际route5已通过。

## 下层能做什么，哪些守卫来自上层

Native26的`build/native26-link.rsp:191`仍直接引用`D:/codex-ck3-background-spill/g2-native89-production01/jobs/c0338/native-p0338.obj`；`build/native26.map:4404`把`ArmTacticalDailySentinelV1`归于该obj。`SOURCE-DELTA.json`没有sentinel增量。已有[Native25绝对截止源审](evidence/native25-absolute-date-deadline-source-review-2026-10-19.json)绑定该obj SHA256 `509b2ce18244d5e107a07cd0fd619643e5d085aff61e42338c2c2da4031eb734`及compile receipt；本次读回其固定`ck3-sdk91/.../src/tactical_daily_sentinel_v1.cpp`仍为SHA256 `25f16c2d21bba1a040abff4bc2876366109dcfdcb70aa9307d7ecc9cbde889a5`。

原生parser 554–569与Arm 599–609允许speed1–5、正向24倍raw目标。`ProcessTacticalDailySentinelAfterTickV1:795–881`检查日期必须逐日+24、同GameState/Jomini、原生暂停、已登记Army/Combat指纹及截止；**没有按speed3或5改变检查的分支**。`PauseAtStableBoundary:354–386`在同Jomini/player调用SetPaused并实际读回paused；基础设施故障发布failed。speed字段是请求/回执绑定，不是绕过Python实际速度读回的替代证据。单一sentinel slot必须保留，不能另Arm一个时钟覆盖原watch。

当前typed exact route在`_advance_exact_day_with_sentinel:25334–25478`使用`start+24`、`mode-terminal-a-0`，**native watch为空**。因此不能声称它逐日原生监视完整敌我Army/Combat：这部分安全由fresh route proof及暂停后重观测承担。原证明`33352–33530`绑定当前date/native与public revision、snapshot、connection generation、episode、主体起点/目标/完整剩余路线、完整hostile集合；`33983+`还拒绝其他未隔离风险军队。每次+1日后旧proof失效，下一日必须使用新帧。

精确helper仍实际setter+速度读回→一次Arm→resume→paused或owner-bound modal→Status，复用原Arm/Stop validator核generation、目标、speed、mode、tick、零过冲与暂停所有权；外层还拒绝超过+24。模态在目标前中断时按同generation cancel，不虚构1日。普通事件沿原typed event-query路径继续；native a0本身不监视event instance，不能从generic事件样本外推exact route5全部弹窗变体。当前合同下无法验证的零日/未知状态仍保留原失败及清理语义，不为提速放宽。

## 最小可施工后继与代价

1. 仅为`_execute_route_contact_horizon_advance`的**fresh contact_free exact-day**增加默认关闭、显式本场配置的speed5试用值；全局`route_contact_timeline_speed=3`、`allow_route_contact_high_speed_ab=False`及各原scope readiness保持原值。进入原exact clock，目标+24、a0、事件/模态和所有proof/validator不变；receipt明示独立scope、配置来源、实际速度。不得只把全局默认改5，或把scope readiness布尔置true。
2. 在源冻结前补少量实际Driver→Protocol软件复现：真实query→fresh proof→typed advance分别跑3/5，除速度/政策receipt外关键结果及命令生命周期一致。用原测试fixture扩展，不另造资格框架。负例覆盖无专用配置仍3、陈旧date/revision/敌军集合/路线变化、其他风险Army、不完整proof、setter/Arm错速度、原生过冲、未暂停/错generation、零日模态cancel；不可避免接触/identity materialization仍1，其他route-window/committed/hold/battle仍原速。月界与终点不越过，不加查询或resume。
3. 软件通过只授源组合资格。后继正常维护冻结采用时，第一次自然fresh contact_free route5需要保留原Arm/Status和既有前后MET：实际speed5、start→start+24、一次resume、同generation、零过冲、实际paused、前后当前路线/Army合法且未重放未知动作。自然到达/路线变更、接触或事件边界各自保留实际处理与下一轮fresh规划证据；缺少的变体仍unknown，不能一条成功升级所有战斗speed5。无需为本研究暂停当前Game或立即额外取样。

代码预计只涉及一个显式配置接缝、一个contact_free preference选择点与receipt，复用既有Native26，不增加每AUTO RPC、不重建DLL、不改变战争候选或游戏日horizon。主要成本是少量Driver/Protocol定向用例和等待自然边界实证；观察失败时保留实际日期/ACK，后续冻结撤回本场专用试用，不重放原动作。

FULL1213实测12次resume→paused共12.8518825秒/12日；route工具总15.2288166秒，整片段29.866188秒。即使把该12.8518825秒全部移除，其他既有工作仍17.0143055秒，即1.417859秒/日。因此route5值得后继验证，但单独它无法让这个片段达到1秒/日；速度5实际受引擎负载影响，不能把速度数字比率当实测收益。不得把累计phase的37秒叠加，或把平时generic5吞吐代替此typed route时钟。

本次交付状态：**SOURCE_REVIEW_ONLY / ROUTE5_LIVE_UNKNOWN**。保留当前route3、A/B和原战争资格；没有源码补丁或当前运行采纳请求。
