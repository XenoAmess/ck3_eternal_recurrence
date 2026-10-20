# 战争四期研究：游玩智能体参考入口

> 2026-10-20追加；machine_id: `desktop-3fevhd2-1c74096080`；来源为Root18:10Z裁定、CI18:14:28Z闭场及fixture18:20:04Z实际回执。

R05正式镜头仍须来自新罗贝尔正常campaign自然接近低补给阈值的输入。R211受控低库存预置后的337供给扣兵、另67围城/劫掠扣兵仅作机制补充，净少404不能全算供给；自然日callback不改变受控输入身份。继续按实际stock/grace/fleet与原生physical结果判断。正式进度保持5/11；[最终裁定与后续合法观测边界](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r211-r05-supplement-review-a01/README.md)。


这些研究同时服务于游玩智能体和影片。智能体开发者及能读取仓库文件的规划代理，可以沿本页取得机制、输入合同、生产消费者和原始证据；研究文档本身不会被普通 `plan/auto` 自动加载为策略。是否已进入运行时，必须看实际代码调用，不能由文档存在推断。

## 怎样读取和使用

1. 先读[当前执行图](episode04-current-execution-map-12004.md)，确认最新结论和未闭问题；旧专题内带日期的 pending 和完成度保留历史范围。
2. 根据下面的决策问题进入机制专题，核对 exact build、EXE SHA、原版输入/调用链和 unknown 分支。
3. 通过现有 MCP 获取本场新鲜输入，交给已有合同/消费者。`ck3_query_army_strengths` 默认 `ordinary_core_v1`；需要保留的事件 journal 时明确选 `observed_history_full_v1`。保存完整结构化返回及同帧身份，文本摘要不能代替原 journal。
4. 将机制判断用于规划。提交动作后独立读取实际结果；ACK、预估、预算、单元测试和历史样本分别使用。文档没有授予当前场次动作资格。

## 按决策问题查知识

| 智能体要回答的问题 | 机制、代码和实际证据 | 可以使用的范围 |
| --- | --- | --- |
| 当前补给风险是什么，下一步需要哪些输入？ | [饥饿与更新顺序](episode04-starvation-loss-12004.md)、[当前 callback 投影](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_callback_supply_risk_projection.py)、[Service 消费](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) | Service 的军队查询实际调用投影并发布 `current_callback_supply_risk_v1`；条件预算不是已经扣除的兵员，也不是完整未来模拟。 |
| 这次跨县究竟扣了哪些兵？ | [县入境机制](episode04-county-entry-loss-12004.md)、[生产 direct-v2 消费者](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_primary_direct_owner_12004.py)、[R0217 原件和结果](episode04-r0217-direct-debits-and-normal-close-20261020.md) | 可复算17次个别直接调用、扣兵小计236及5次排除；县总额仍 null。这是原因识别和证据消费，不是所有县通用损耗率或普通 planner 已采用该小计的证明。 |
| 低库存实际损失和围城损失如何区分？ | [R211 自然 callback 与离线重放](episode04-r211-zero-stock-physical-12004.md) | 同一实际窗口供给337、围城/劫掠67，由生产 join/selector/classifier 分开；受控初始化不当自然耗尽，404净差不全部归为饥饿。 |
| 移动已锁定时还能怎样 Halt 或改道？ | [原生判据和接口](episode04-locked-halt-reroute-12004.md)、[R12 已锁定 Halt 实证](episode04-r12-locked-halt-r0175-12004.md)、[R13 已锁定改道实证](episode04-r13-locked-reroute-r0176-12004.md) | 用同帧实际 progress 与 loaded cutoff 的严格比较，实际路线和后来到达分别判断；不能假设 Halt 立即原地停止。早期机制页的待实测说明以其当时日期解释，后继实证从当前执行图进入。 |
| 拆合军后怎样估算库存、容量和统帅影响？ | [库存权重与取整顺序](episode04-split-merge-stock-weight-order-12004.md)、[S端 flags0 权重](episode04-merge-source-weight-flags0-12004.md) | 分别读合前 D/S 权重与库存、合后实际统帅和容量；按已证分阶段整数运算比较。人数简单平均、候选统帅容量或相等边界不能替代实际 clamp。 |
| 能否把补员开关或人数增长当实际补兵 ADD？ | [实际应用合同](episode04-refill-application-12004.md)、[R0221 同次 Core 离线恢复](episode04-r0221-target-add-offline-recovery-12004.md)、[公共单日入口](episode04-r06-public-one-day-and-a40-boundary-20261020.md) | R0221 已证明选定 Regi2602/slot1 的指令 ADD 为 68→69；画面整军 +10 另记。原 live consumer 的大小限制失败保留，完整 Core NET、开关效果及全 R06 仍未闭合。公共研究入口尚未成为普通 planner 策略。 |
| 当前维护费向量能否视为实际付款？ | [十槽向量与分量保留](episode04-r08-current-vector-component-retention-12004.md)、[R08 公共研究入口](r08-writer-common-public-entry.md)、[R0222 失败与行政闭场](episode04-r0222-failed-writer-and-administrative-close-20261020.md)、[R0223 实际一日与未闭付款归因](episode04-r0223-one-day-no-cd-and-normal-close-20261020.md) | 资源槽、当前费率、实际扣款、付款方和周期分别判断。R0222 0 日、无 writer，独立 payment OFF 读回未知；后续退出或源码修复不能补成付款归因。 |
| 休整点是否真的恢复携带补给？ | [被动库存证据合同](episode04-b-stock-passive-evidence-12004.md)、[实际机会与 journal 边界](episode04-r10-stock-growth-opportunity-12004.md) | 用同 Army、同地点与自然日期的真实库存正差分及实际 callback 判断；eligible/gain 分量、兵员补员或同值端点都不能替代库存增长。当前合格 B 点仍为 0/2。 |

## 可用性与运行时边界

新增可直接复用的专题：[B 驻地库存被动证据合同](episode04-b-stock-passive-evidence-12004.md)说明如何只用原场次已采集的一日证据判断驻地，不追加游戏动作；[R08 十槽向量与分量保留](episode04-r08-current-vector-component-retention-12004.md)说明现有查询已经提供什么、哪些资源语义仍未知、拆分两个原生分量还缺什么。两页都绑定源码与原件 SHA，均不增加 B、R08 或 ABC 实机资格。A41 的构建、SYSTEM 精确路径与两项冷测原件见[资格证据](evidence/episode04-a41-native-20261020/README.md)；它们不能代替游戏内 ADD 观测。

- **文档参考已具备**：本页由[原生 AI 主索引](README.md)和[智能体项目入口](../../ck3_autonomous_player/README.md)链接，来源均为仓库相对路径，不依赖影片、作者的工作盘或大原片。
- **部分代码消费已具备**：军队查询的 Service 投影及 direct-v2、R211 等生产消费者可复用。direct-v2 的实际小输入和生产源码 pins 见[R0217投影](evidence/episode04-r0217-20261020/research/DIRECT-V2-PROJECTION.actual.json)、[已有重放入口](evidence/episode04-r0217-20261020/research/verify_portable.py)。本次针对用户问题的[当前源码消费复核](evidence/episode04-agent-knowledge-consumption-20261020.json)单独记录，不新增游戏或业务信用。
- **不会自动变成策略**：普通规划器没有“读取所有 Markdown 并执行”的通路。新增决策行为仍须将专题结论显式实现为 planner/policy 输入与规则，并验证实际结果。不要把实验脚本、prepared 候选或已编译构建视为已部署的自动策略。

跨机器可复用机制、代码和归档输入；源机器的 Steam 离线、安装、权限、进程、空间与实机资格不能继承。新实机独立核 machine_id、实际版本和运行时绑定；来源机器及历史时间以各专题和原件为准。

2026-10-20 补注：R0221 与 R0222 的上述实机记录来源为 `machine_id: desktop-3fevhd2-1c74096080`，观察及精确原件分别在两场专题。表中旧“没有新 R06 实机 ADD”已按后继独立证据更新；不把这次更新外推为其他机器通过或 planner 已自动读取研究。

R08 后继运行源码与已编译组件的关系见[bc638 来源选择](evidence/episode04-r08-runtime-repair-20261020/bc638-runtime-source-selection/CURRENT-SOURCE-COMPONENT-SELECTION.actual-a01.json)：运行 Native 树6b91与历史编译树fee分层；master远端新增的d622不能据此追认已编译。该记录授源码选择与原组件复用边界，不授新场实机或整套R08资格。

## 2026-10-20 R0223后可直接用于战争预算的规则

当前维护费率为正时，可以作为预算输入，不能称为已经实付。Army自然parent阶段已发生，也不能据此认定Character维护结算被选择。targetcache或paidjournal为空不授权“军费0”；保持付款unknown，继续使用本场来源明确的原生费率、钱包与已有承诺做战争预算，保留雇佣应急资金，输入不足时延后可选建设。

来源机器 `machine_id: desktop-3fevhd2-1c74096080`；[R0223原件、结果和研究边界](episode04-r0223-one-day-no-cd-and-normal-close-20261020.md)分别记录真实一日、两次Army parent、C/D未取得和正常闭场。研究文档可供规划代理阅读，尚未实现的候选不会自动成为普通planner策略。正式动态镜头当前4/11（R04/R06/R09/R12）；完整R08、B0/2与ABC0/3均未新增资格。

## 2026-10-20 parent-entry候选的运行边界

当前运行链没有接入该Character parent-entry hook。独立default-OFF源码候选、源码检查和合成fixture不代表生产Native已编译、安装、接入public startup或取得实机付款结果；可复用知识仍需通过已存在的当前原生接口输入规划。当前维护费率可供预算，null付款、空paidjournal或未选中维护结算机会都不能推导“军费0”；继续用本场费率、钱包、已有承诺与雇佣应急资金处理战争，缺输入时延后可选建设。

机制、最终来源pins和独审install-gap从[候选与冷测边界专题](episode04-r08-parent-entry-candidate-and-cold-boundary-20261020.md)进入。研究文档不会被普通planner自动读取执行；未集成、未编译状态不能据此升级为可用能力。

## 2026-10-20 17:22 UTC 镜头账本与战争预算边界

当前正式动态为5/11（R04/R06/R07/R09/R12）；R0196仅签登船源[32,52)秒，3金币的原生个人钱包扣款有同场绑定，不是维护费或所有登船的通用报价。未观测付款保持unknown，不能由null/空journal推0费；当前原生费率与钱包仍用于战争预算。此前4/11及未编译候选说明按其快照时间保留；后继独立编译尝试不能追认旧prepared packet或自动成为生产可用hook。

## 2026-10-20 17:35 后继独立有限冷验

`machine_id: desktop-3fevhd2-1c74096080`。Root已接受独立a04组件/修正fixture-a03的有限冷验：真实MSVC静态库与一cold EXE、该EXE精确SYSTEM设置读回、四mode原wait0，以及实际90个合成CONTEXT指令PC的Windows RtlVirtualUnwind通过。[冷验专题和原件](episode04-r08-parent-entry-selected-cold-20261020.md)区分第一次MASM A2022失败、窄operand-width修正、后继成功与Root验收；这不是整个bc638/master Native重编译。

前述17:14源码包与后续首次失败报告按各自时点保留，不能追认当时已编译。当前运行链仍未接入此hook，真实Install/Restore、受管全线程安装窗口、public admission/typed Snapshot/OFF及游戏付款仍未取得；null付款不推军费0。正式动态5/11、研究10/14、业务7/11、B0/2、ABC0/3及fullR08false不因冷验变化。
