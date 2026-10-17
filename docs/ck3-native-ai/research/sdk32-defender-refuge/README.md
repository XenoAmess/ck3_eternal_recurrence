# 单县防守的同境撤离候选

SDK32窗口27的原AUTO2086没有下单：`native_war_no_alternate_player_held_county`只列当前省2619，敌军已经指向这里。窗口从raw53436984推进到53480760，共1824日后失败；后续SEM2087、零RPC清理2088和SDK正常0/0退出独立保留，Game／OBS未停止。此时角色为39979，不将后续角色行为写成罗贝尔本人战果。

公共最小修复扩充**只读候选**：只有同帧完整campaign-root、完整直辖封臣上下文、单直辖县的主防守方，以及我方唯一可控、静止、非战斗／非撤退军队，才向既有Native能力公开该境直辖封臣的首都预览／移动／接触查询种子。七个实际首都为2604、2610、2614、2623、2628、2631、8755。候选不证明邻接、原版移动合法、当前战争立场或路线安全。

普通Strategy先选原版路线预览；真正移动仍须原exact路线及完整敌军接触后验，主动攻击1.5倍门槛不变。逐个预览明确deferred时只排除该目标，继续其余候选；全被拒则回到当前省的零跳Native接触查询，不伪造contact-free，也不直接推进未知路线。

五个便携测试使用正式公共NativeDriver和ProtocolState；实际public2464与Native5729分别保留，真实Service.plan_turn选择readonly preview2604。四类旧帧／actor／连接／Native修订负例不公开新候选；所有预览deferred的用例通过合成完整query历史输入验证零跳退路，没有替换Strategy helper。连同围城防守／负接触／继续风险回归共26项、2子用例通过。

164KB实际字段投影只保留封存history的380至392，共13条记录和SEM；不复制5.95MB完整history，不混入故障后mercenary索引393。索引382的原举兵及383的第一次独立root读回必须保留，才能重现原rally-hold守卫；删掉这些证据时规划应先读当前省接触范围，不能为了断言preview而跳过守卫。测试ProtocolState/cache为明确重建，Native I/O没有执行。

这证明公共源码与离线普通规划链，**不证明AUTO wire执行、成功撤离、安全移动或实机后续稳定**。原冻结FINAL里Service为PENDING是旧测试截点；本批公共五项已通过真实Service入口，但不追改该原件。SDK33的创建／启动由现场owner管理，公开提交不改变D盘冻结源。

- [原冻结FINAL](FINAL.json)、[公共源pins](SOURCE-PINS.json)
- [SDK32 Strategy窄patch](strategy.py.patch)、[Driver窄patch](bridge-native_driver.py.patch)、[公共路径patch](PUBLIC-REFUGE.patch)
- 测试：`ck3_autonomous_player/tests/unit/test_defender_refuge_candidates.py`
- [实际失败交接](../../../handover/2026-10-17-p27-native21-continuation.md)
- [同期有限性能／CB研究](../sdk32-peace-and-cb-offline/README.md)只作离线报告，不混入本次玩法修复。

30年稳定优先，其后<1秒／日、再0.5秒／日，均未达；本包没有新Native能力、WAL或新游戏／录像限额。

## 提交前追加：SDK33实际出发链与后段失败

Root的[实际链小原件](ROOT-P33-ACTUAL-DEPARTURE-CHAIN.json) SHA `64228d8e1f0766acac3eddea995825b598db733f838ee83b17f4657d640c7cbc`绑定同Game6068／出生FILETIME：AUTO16原生预览、19完整horizon、22移动、独立SEM24、clock29以及fresh31/32均真实成功，没有Game／OBS重启或原动作重放。此前“未验”是离线测试自身边界；现在有独立实机出发链，不能把它仅称为候选。

后续实际到达封臣2604，但FULL178／AUTO191在`native_war_counterpolicy_hold`再次无动作阻塞。窗口28失败31日，raw53481528／Native5831／public103／12157cycles。helper只对原单直辖县／rally-hold起点提供候选，尚未闭合到达后的驻守与再次撤离生命周期，另由SDK34修复。原窗口27的1824日与窗口28的31日各自保留，不能拼成连续验收。本包不声称全面稳定或30年达标。
