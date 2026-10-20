# 战争四期研究：游玩智能体参考入口

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
| 能否把补员开关或人数增长当实际补兵 ADD？ | [实际应用合同](episode04-refill-application-12004.md)、[公共 R06 单日入口与当前资格边界](episode04-r06-public-one-day-and-a40-boundary-20261020.md) | 开关、准备量、请求量、指令 ADD、实体变化分别判断。公共 R06 是研究/验收入口，不是已经接入普通自动游玩策略；当前没有新 R06 实机 ADD。 |

## 可用性与运行时边界

- **文档参考已具备**：本页由[原生 AI 主索引](README.md)和[智能体项目入口](../../ck3_autonomous_player/README.md)链接，来源均为仓库相对路径，不依赖影片、作者的工作盘或大原片。
- **部分代码消费已具备**：军队查询的 Service 投影及 direct-v2、R211 等生产消费者可复用。direct-v2 的实际小输入和生产源码 pins 见[R0217投影](evidence/episode04-r0217-20261020/research/DIRECT-V2-PROJECTION.actual.json)、[已有重放入口](evidence/episode04-r0217-20261020/research/verify_portable.py)。本次针对用户问题的[当前源码消费复核](evidence/episode04-agent-knowledge-consumption-20261020.json)单独记录，不新增游戏或业务信用。
- **不会自动变成策略**：普通规划器没有“读取所有 Markdown 并执行”的通路。新增决策行为仍须将专题结论显式实现为 planner/policy 输入与规则，并验证实际结果。不要把实验脚本、prepared 候选或已编译构建视为已部署的自动策略。

跨机器可复用机制、代码和归档输入；源机器的 Steam 离线、安装、权限、进程、空间与实机资格不能继承。新实机独立核 machine_id、实际版本和运行时绑定；来源机器及历史时间以各专题和原件为准。
