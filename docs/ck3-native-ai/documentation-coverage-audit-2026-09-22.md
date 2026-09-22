# CK3 原生决策树文档覆盖盘点（2026-09-22）

本次盘点基于任务开始时 fetch 得到的远端 `master`：
`0d7d4af1012127b10ace350582ee220d986dd418`（提交时间 2026-09-22 17:23:59 +08:00）。
独立 detached worktree 为 `D:/workspace/ck3_native_tree_docs_audit_20260922`。
统计与评分固定在这个基准，后续入库提交不改变该快照的含义。

结论：原生军事 AI、通用事件选择器和部分专门脚本树已有较深梳理；内政各域深浅不一，
尤其要区分完整 AI 选人/择时/排序与已实现的玩家状态读取、命令接口。
目前没有 CK3 全部原生分支的完整清单，不能负责任地给出“整个 CK3 已逆向 X%”。

## 口径

这里的“决策树”指原生 AI 行为逻辑及其配套引擎状态机，包含原版随附 DLC；不是只数决议菜单。
底层专题绑定 CK3 `1.19.0.6` 与 EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
本次审阅已有 docs、机器记录和 registry，不启动 CK3，不把旧实机证据称为本次重新验收。

主表百分比是**本次审阅的文档梳理成熟度评分**，不是统计意义上的原生分支覆盖率、
AI 行为复现率、MCP 完成率或实机通过率。五项各取 `0/1/2`：

| 项 | 检查内容 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|---|
| S | 版本与来源 | 未绑定 | 只有入口/版本描述 | exact-build 来源、脚本/调用链有可追溯证据 |
| T | 触发与候选 | 未梳理 | 局部入口、候选或调度 | 声明范围内触发/候选有实质展开 |
| G | 条件分支 | 未梳理 | 部分门槛，关键分支未知 | 主要资格/拒绝/分叉有实质展开 |
| W | 权重与选择 | 未梳理 | 参数/部分评分已知 | 主排序、权重或随机选择规则已展开 |
| O | 输出与后果 | 未梳理 | 命令入口或部分结果 | 主要执行/效果/状态转移有实质展开 |

`成熟度 = (S+T+G+W+O) / 10 × 100%`。2 分表示该维度有实质分析，不保证穷尽；
评分仅用于阅读和施工定位，粒度为 10 个百分点。表中范围不同、彼此重叠，不取平均、不合成全游戏总分。
所有评分同时保留主要未知项；有关键未知的专题不评 100%。

基准中 `docs/` 有 **795** 份受 Git 跟踪的 Markdown；`docs/ck3-native-ai/` 有 **283** 份，
其中 **135** 份含 Mermaid，共 **330** 个 Mermaid block。这些只是文档规模，
包括接口、工具、我方策略和 mod 专题，不能解释成 283 棵已完成原生 AI 树。

## 军事 AI

| 原生树及评分范围 | S/T/G/W/O | 成熟度 | 已梳理内容 | 主要缺口与证据边界 |
|---|---|---:|---|---|
| [宣战](war-declaration.md) | 2/2/1/1/2 | 80% | 人格/周期/冷却、目标和盟友军力、CB 资格与评分、90% 截断、Top-5 加权随机、提交顺序 | 人质完整真值表、财政/军力细项、完整 CB 分数账本仍缺；有最终 validator 局部实证，不能算自主宣战全树 live |
| [军队 stance、目标与移动调度](army-controller.md) | 2/1/2/1/1 | 70% | 七类 stance、候选 block 回退、初筛 Top-10、敌军 power 曲线、7/14/30 日参数、分合军阈值与 move 提交 | 最终路径/评分修正/tie-break、部分 timer/invalidation、本地 siege/wait/support 和跨 owner 协调不全 |
| [接战预测、避战与战略退让](combat-prediction.md) | 2/1/2/1/2 | 80% | 确定性战力占比、敌方修正、接战门、坏邻接绕路、求援、无退路分支 | 底层 power 公式、mode/lane 语义、normal/desperate 触发和后续排序未知；该比值不是胜率 |
| [求援与增援指派](battle-reinforcement-and-join.md) | 2/1/2/1/2 | 80% | asking 滞回、同/跨 stack 请求者顺序、候选避战门、目标 Province、move→join→main 反馈 | 上游 Province 候选来源、跨 coordinator 信号、同日 contact/combat 次序仍缺；只读指派 live 不等于 assigned+ETA/join 全部实证 |
| [战中 AI 主动撤退](active-combat-retreat.md) | 2/0/2/0/2 | 60% | 四道合法门、full-side/owner-subset 执行及 pursuit 转换 | 通用战争 AI 的撤退择时、odds→choice caller、目的地评分仍未闭合；玩家命令的撤退实证不能提升这些 AI 选择项 |
| [和平军备](military-preparation.md) | 2/1/1/1/1 | 60% | 预算、MAA 与建设竞争、兵种质量/围城配比、个人/头衔 MAA、恢复与雇佣参数 | scheduler、完整选兵评分、骑士/统帅比较器、雇佣兵市场排序及和平处理不全 |
| [战争结束：执行要求、白和、投降](war-termination.md) | 2/1/2/2/2 | 90% | 三种主动提出与独立接受树，战分/时长/债务/其它战争/人格/人质，auto-accept；claim_cb、Raiktor 条款深入 | 真正发送调度日、通用互动子门与全部 CB 不能外推；具体战争条款/终局已有 live，未穷尽自然 AI 提议 |

行号定位（均为本盘点基准）：宣战 `32–66、349–446、523–538`；军队控制 `73–150、304–435、749–763`；
接战预测 `173–350、706–718`；增援 `23–44、162–438、680–698`；主动撤退 `33–66、141–380、580–612`；
军备 `249–340、442–450`；战争结束 `565–667` 及后续 CB 专段。

## 内政、社会与角色 AI

| 原生树及评分范围 | S/T/G/W/O | 成熟度 | 已梳理内容 | 主要缺口与证据边界 |
|---|---|---:|---|---|
| [婚姻、联盟与召集](marriage-and-alliance.md) | 2/1/2/1/1 | 70% | 五角色上下文、发送合法性、对玩家反算接受度、主动候选/评分 helper、婚姻/订婚及联盟/召集代表分支 | scheduler、完整候选空间、未命名评分项、tie-break 与选项搜索不全；R736 的 657 个合法首继承人婚配候选没有 native rank，不能称完整择偶算法 |
| [派系危险告警与赠礼回应](factions-and-rebellions.md) | 2/1/1/1/1 | 60% | 既成派系力量/不满度与危险条件、12 类后果；给派系封臣赠礼的目标/频率/门槛/费用/好感 | 不是完整派系创建/加入/退出/叛乱 AI；最后通牒组合门、完整主动决策仍缺，参见 [targeting factions](player-targeting-factions-v1.md) |
| [内阁选人、换人](council-composition-ai.md) | 2/1/2/0/2 | 70% | 职位适用、候选合法性、自动填充、任命/替换/交换/解职、强力封臣和解职代价 | 综合效用、输入权重、cadence、同分选择未知；GUI 技能排序不是 AI 选人公式，11/11 候选身份读取也不是评分实证 |
| [内阁任务通用框架](council-and-development.md) | 2/1/1/1/1 | 60% | 15 种职位 vocabulary、任务类型/进度、ai_will_do、目标正权重随机、默认任务 | scheduler、fallback、全部任务公式未齐；R639 当前 active task 的 live 读取不证明完整派工策略；与下一行重叠 |
| [总管发展县/收税](steward-develop-county-ai.md) | 2/1/2/1/2 | 80% | 收税/发展权重顺序、储备阈值、地形/文化/发展上限过滤、回默认任务、5/15 年冷却 | 完整任务池/最终抽样、完成和冷却重评顺序未知；缺 ai_target_score 只证明随机，不能擅自称均匀 |
| [直辖建筑新建/升级](domain-construction-ai.md) | 2/1/2/2/1 | 80% | 四层合法门、动态 ai_value、最佳分 80% 入围带及带内加权抽选、严格成本比较、提交/队列、completed daily tick→AI manager | 每 owner cadence、候选子类语义、资源全映射、存钱状态生命周期、完工重评延迟仍缺；静态路由不是完整 AI 建设 trace |
| [文化创新/迷恋/传播](culture-innovation-ai.md) | 2/2/2/1/2 | 90% | 108 项创新库存与 fascination 模板、30 桶月度调度、可推进门/重选/加权选择、时代与研究进度 | spread 权重 fallback 未全闭合；不包括文化分化/融合/传统的完整 AI 树 |
| [法律、契约与继承法](laws-contracts-and-succession.md) | 2/1/2/1/2 | 80% | law group、适用/可通过/费用、正分最高法、默认/继承/失效替换；王权和继承代表链；契约相邻级、desire 改善后加权随机 | scheduler、同分、假设改法后的继承分配、完整契约 preview 等不全；不是每一条法律逐项覆盖 |
| [生活方式、重心与 perk](lifestyle-focus-perk-ai.md) | 2/1/2/1/2 | 80% | 15 个普通重心权重/输出、6 棵外交/管理 perk 父图、新树门/后继权重、60 月冷却、Wanderer 年度转向 | 后续重选、花点 cadence/tie-break、其余 perk 树与 DLC 收益不全；R757 当前状态读取 GREEN 与 R764 候选 RED 应分别看待 |
| [囚犯、犯罪、赎金与刑罚](prisoner-crime-ransom-ai.md) | 2/1/2/1/2 | 80% | 12 个 prison interaction、逮捕、三种赎金角色、释放/处决/刑罚候选、频率、主要权重/hard-zero、tyranny | modifier 未全部逐项展开；容器/option ownership、所有惩罚后果仍需补，窄 pay_ransom 拒绝实证不等于整域完成 |
| [非宗教谋略](nonreligious-schemes-ai.md) | 2/2/2/1/1 | 80% | murder 五年 pulse、sway/abduct 调度、每日有效/月度推进、agent/机会/执行门、成功/拦截/保密独立结算 | 其他 definition 家族、通用结果关联、agents/critical moment 完整策略未齐；private binder 不能作实机树证据 |
| [宴会、狩猎与巡游](non-religious-activities.md) | 2/2/2/1/1 | 80% | 可见/计划/开始/持续有效、最高分>20 再概率 roll、频率/地点加权、三活动门槛/费用/阶段、host/join 入口 | 完整选项权重、邀请集合、HostView evaluator、phase/结局 native surface 和 payload 不全；不包括全旅行系统 |
| [首批核心外交提案](core-diplomatic-proposals.md) | 2/1/2/1/2 | 80% | 11 交互的机会/接受度/后果、多角色/选项、Can Send、发送/最终答复链 | scheduler/抽样/tie-break、各交互完整权重不全；朝贡四交互仍是相邻账本，不冒称中国外交全覆盖 |

正文定位：婚姻 `616–767、812–846`；内阁选人 `49–126`；内阁任务 `124–142`；总管 `27–134`；
建设 `227–310、561–640`；创新 `35–119、211`；法律契约 `43–118、176`；生活方式 `71–236、717–879`；
囚犯 `27–197、288`；谋略 `61–184、259`；活动 `39–175、256`；外交 `30–133`。

## 通用事件、互动与明确的单项决议

| 原生树及评分范围 | S/T/G/W/O | 成熟度 | 已梳理内容 | 主要缺口与证据边界 |
|---|---|---:|---|---|
| [通用事件选项 selector](events-and-interactions.md#原生-ai-的事件选项树) | 2/2/1/2/2 | 90% | authored 顺序、trigger/exclusive/fallback、两种权重优先级、取整、正权重区间/全非正均匀选择、返回 index 与 effect 路径 | context-mode 的业务语义、上游 RNG stream 身份及完整动态效果预览仍缺；不是所有事件内容都已分析 |
| [通用人物互动发起/接受/回复](events-and-interactions.md#原生-ai-的主动人物互动树) | 2/1/2/1/2 | 80% | frequency/targets/options、Can Send 12 步、组合取最高分、发送概率、intermediary/recipient/auto-accept/reply 分流 | production scheduler、抽样/tie-break、完整 special subtype 副作用与结构化条款仍不全 |
| [建立新王国](major-decision-found-kingdom.md) | 2/1/2/2/2 | 90% | duchy 每 60 月候选、资格、四态费用矩阵、固定 100% AI 分数、建国与法理/事件效果 | 仅 `found_kingdom_decision`；AI due-date/RNG 调度仍缺。后续 [submit ABI](major-decision-found-kingdom-native-submit-abi.md) 已补命令链，[private route](major-decision-found-kingdom-internal-route.md) 仍缺生产 capture 绑定与动作实证 |
| [封臣转封](title-vassal-transfer.md) | 2/0/2/0/2 | 60% | `grant_vassal_interaction` 资格、接受/拒绝分支、停战/好感、原子 change_liege 结算 | AI 发起者 entirely-through-code 的候选/评分仍未知，C++ special 副作用未全部展开；收到/拒绝提案的切片不等于会自主选人转封 |

事件 selector 的关键正文在 `events-and-interactions.md:174–235`，通用互动在 `295–359`；
建国 source 在 `major-decision-found-kingdom.md:44–121`。建国总页开头“没有实现 bridge/action”是旧阶段边界，
本次已结合后续 ABI/private route 文档，未将其当作当前实现全貌。

## 配套引擎规则：单列，不混入 AI 选择评分

| 配套树 | 梳理程度 | 仍缺什么 |
|---|---|---|
| [逐日移动与接触](army-contact-resolution.md)、[actual contact](actual-contact-scope.md) | 较完整：movement queue、已有战斗选择、新建战斗对手/参与者顺序与攻守极性；正常建战与冷恢复有实证 | non-daily 入口统一全序、manager 排序来源、多个 compatible battle / join-existing 的完整 live 矩阵 |
| [战斗 phase、伤害与追击](battle-simulation.md)、[phase events](combat-phase-events.md) | 深入：phase/day tick、战宽、roll、advantage、counter、soft/hard casualty、pursuit、PRNG 与 stock 13 项 phase-event AST | 动态 modifier/effect、伤残死亡后同日刷新、增援顺序、完整原生差分 trace；[模拟器](combat-simulator-core.md) 仍明确 `fidelity_gate=false / planner_usable=false` |
| [战斗终结、清理与重新接敌](battle-terminal-and-reentry.md) | 较深入：normal/no-normal 分叉、warscore、backlink cleanup、residual rescan、幸存 AI assignment 重入 | invalidation 上游来源/节拍、同日全局次序、结果 effects；normal terminal 有实证，余下三类终局 live 矩阵未齐 |

## 可给出真实分母的局部统计

| 库存/记录口径 | 分子/分母 | 比例 | 不能外推的结论 |
|---|---:|---:|---|
| [stock 创新 fascination 权重模板](culture-innovation-ai.md) | 108/108 | 100% | 不是整个文化系统或全部创新 AI 分支完成 |
| [十五个普通重心的权重/持续输出表](lifestyle-focus-perk-ai.md) | 15/15 | 100% | 不是所有 perk/DLC 树完成；本专题另展开 6 棵外交/管理 perk 父图 |
| 当前 registry 有 analysis metadata 的 key | 193/193 | 100% | 迁移说明也算 metadata，不等于逐条完整源码分析 |
| 当前 registry 有 observation metadata 的 key | 193/193 | 100% | 大量 metadata 仅为旧合同迁移，不能作当前 live 证明 |
| analysis 有非空且格式合法的 source SHA-256 字典 | 124/193 | 64.25% | 本次只核对字段存在/64 位十六进制格式，没有重新哈希全部原版文件 |
| 至少有一个非 legacy exemplar 的 key | 54/193 | 27.98% | 包括 pre-action RED、visual RED、degraded 和 GREEN；**不是实机成功率** |

余下 69 条 analysis 没有该 source hash 字段，139 个 key 只有 legacy exemplar。
不能从 metadata 标签机械计算全库实机通过率：例如 `chancellor_task.1004` 的非 legacy 记录只有视觉 harness RED；
反过来，草药种子与交友结局的物质后置已见于专题，metadata 尚未完整反映。

本轮发现的旧计数：`README.md:180–181` 为 `182/38`；
`vanilla-event-knowledge-registry.md:8–9` 为 `184/43`，同页后续又有 `188`。
当前静态模块实际组合及 `test_vanilla_event_registry_migration_parity.py:385–386` 则是 **193**。
旧数字保留其历史含义；本报告以此基准的实际数据为准，没有批量改写历史记录。

复现时在本报告基准 checkout 中运行下列 Python；仅 import 项目静态记录，不连接游戏：

```python
import hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "ck3_autonomous_player/src"))
import xar_autoplayer.vanilla_events as v
data = json.loads(json.dumps({
    "contracts": {k: x for g in v.DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS for k, x in g.items()},
    "analysis": v.DEFAULT_VANILLA_EVENT_ANALYSIS,
    "observations": v.DEFAULT_VANILLA_EVENT_OBSERVATIONS,
}, ensure_ascii=False))
print([len(x) for x in data.values()])  # [193, 193, 193]
print(sum(any(e["kind"] != "legacy-live-binding" for e in x["exemplars"])
          for x in data["observations"].values()))  # 54
print(sum(bool(x.get("source_sha256")) and all(re.fullmatch(r"[a-fA-F0-9]{64}", s)
          for s in x["source_sha256"].values()) for x in data["analysis"].values()))  # 124
blob = json.dumps(data, ensure_ascii=False, sort_keys=True,
                  separators=(",", ":"), allow_nan=False).encode("utf-8")
print(len(blob), hashlib.sha256(blob).hexdigest())
```

该三层 canonical JSON 为 `689856` bytes，SHA-256
`7b34a8d3d760cb5db8c0619776adb516436a9588fb2727ceee5989b0c5f7a7ee`。

## 具体原版事件专题清单

以 `docs/ck3-native-ai/*.md` 首行包含 stable event key（`[a-z_]+\.[0-9]{3,}`）为可复核库存口径，
共 **31 篇、38 个主事件键**。一篇疾病链有八个主键；不计其 caller/后续子节点，也不覆盖 registry 中所有键。
已有宗教通知只登记存在，不开展新研究。这些页多数深入到选定事件的 source、scope、候选、选项/权重和后果；
因此按事件逐项读很有价值，但不统一套一个“全库逆向百分比”。

| 组 | 页/主键 | 已有专题与范围 |
|---|---:|---|
| 疾病诊断/治疗链 | 1/8 | [health.1001/1006/3001/3101/3102/3103/1106/2202](health-consumption-diagnosis.md)：触发、求医、治疗/康复分叉；R416/R418 多段有选择后置，其他疾病/投影不能外推 |
| 普通康复与衰弱 | 2/2 | [health.1101](health-1101-ill-recovery.md)、[health.7000](health-7000-infirm-onset.md)：调用、trigger、immediate/option 区分；当前不同投影仍有自然 RED |
| 哀伤与继承人死亡 | 2/2 | [stress_threshold_special.1001](stress-threshold-special-1001.md)、[death_management.1007](heir-death-stress.md)：九选项/显示门及死亡通知压力；R0071 哀伤压力 100→64 见当日日报，不能据旧页 R0065 摘要认定从未实测；永久 modifier 与 .1007 物质后置仍须分别核验 |
| 疫病治理 | 5/5 | [epidemic_events.0110](epidemic-events-0110-recovery.md)、[.1020](epidemic-events-1020-flowers.md)、[.1100](epidemic-events-1100-outbreak-notice.md)、[.5007](epidemic-events-5007-herbalist-accusation.md)、[physician_epidemic_events.1000](physician-epidemic-events-1000.md)：人物/县候选、选择成本、后续效果；历史 drain 不替代当前物质读回 |
| 年度与家族 | 5/5 | [yearly.0003](yearly-forbidden-love.md)、[yearly.1030](yearly-hook-for-secret.md)、[bp1_yearly.1040](bp1-yearly-bathhouse-friend.md)、[bp1_yearly.4000](bp1-yearly-family-memory.md)、[bp1_house_feud.0014](house-feud-cuckold-reveal.md)：年度池/冷却、关系分支、选项与副作用，部分投影有 live |
| 特质事件 | 3/3 | [trait_specific.4001](trait-specific-witch-encounter.md)、[.8001](trait-specific-herbalist-seeds.md)、[.9001](trait-specific-poet.md)：调用/权重、一次或重复、四种女巫 scope 形状；草药种子 R664 有金币后置，诗人 R856 只查询 |
| 思潮互动 | 4/4 | [tgp_movement_events.0030](tgp-movement-support-letter.md)、[.0060](tgp-movement-rival.md)、[.0070](tgp-movement-shared-scroll.md)、[.0110](tgp-movement-book-gift.md)：caller/人物选择/冷却、AI 性格权重与效果；共读重复实例有实证，实际 caller 归因仍有边界 |
| 王朝周期与日本年度 | 3/3 | [tgp_dynastic_cycle_events.0001](tgp-dynastic-cycle-advancement.md)、[tgp_dynastic_cycle.0072](tgp-dynastic-cycle-stability-notification.md)、[tgp_japan_yearly_events.1190](tgp-japan-yearly-1190-night-decisions.md)：关系投影、阶段通知、三条夜间选项风险；不同路线有不同 live 状态 |
| 文化分歧通知 | 1/1 | [culture_notification.1111](culture-divergence-notification.md)：on_action、scope/ethos、重复确认；不能外推完整文化分化 AI |
| 宝物强化 | 1/1 | [artifact.4040](artifact-expert-improvement.md)：年度池、30 年冷却、宝物/专家筛选、词条与费用；选择后置不代表全部随机词条实测 |
| 交友结局 | 1/1 | [befriend_outcome.0002](befriend-outcome-0002.md)：success/failure 投影；success R861 有压力/事件/下一 turn/checkpoint，failure 尚有独立缺口 |
| 叛乱参战来信 | 1/1 | [char_interaction.0232](char-interaction-0232-rebel-war-call.md)：三个 caller、参战/拒绝与好感；完整战争后果不在这个切片内 |
| 科举家族通知 | 1/1 | [imperial_examination.7100](imperial-examination-family-notice.md)：殿试/会试/落榜优先级、scope 与选项；三种投影没有全部 live |
| 历史宗教通知 | 1/1 | [fervor.1002](fervor-1002.md)：只列旧专题存在，宗教专项继续暂缓 |

## 尚未建成通用原生 AI 树的范围

以下表示未找到对应完整独立专题，不表示完全没有局部原版知识：

- 教育/监护人、儿童成长与王朝长期规划：外交互动中有教育入口，尚不能代替完整候选评分/成长树。
- 宫廷职位/宏伟度、宝物管理与勋号规划：有战斗输入、单个宝物事件及 [职位薪资机制](../court-position-mechanics.md)，没有通用选用/管理 AI 树。
- 旅行路线/随从/危险与返程：活动与具体旅行事件已有切片，不能等同整条旅行规划树。
- 各政府、无地冒险者、摄政/共治、劫掠等专门战略：有参数、军队任务和接口切片，尚不能计完整专属树。
- 全局长期目标与跨域资源调度：现有 `player-counterpolicy`、G2 与各类 utility 文档是我方策略，不是完整原生总规划器。
- 通用宗教、改宗/改革、教义/信条/热情与 holy order：**owner-deferred**。历史事件记录及战争/婚姻的最小例外不代表解除暂缓，也不计完成。

`campaign-root-context`、DLC manifest、entity directory、GUI locator、存读档、loader/bridge、
`zhongguo-*` 产品验收等文档各有用途，但不单独计成原生 AI 决策树。

## 可复核性与状态限制

全文采用专题正文和较新的窄范围记录校正索引摘要。例如增援文档已经澄清 asking 位属于
`CAISubunitStack`，而旧 `battle-controller` 摘要仍把相关内容列为 unknown；终局专题已经展开
no-normal 的 raw predicate，也不能继续机械照搬旧摘要的未知项。

本次是文档盘点，无 gameplay、ABI、MCP 或 readiness 修改。既有实机证据按原文范围引用，
没有在本机重新检查外部 artifact 的每个字节。文档验证仅检查本报告评分算术、相对文件链接与 diff 格式；
不需要启动 CK3，也不需要 `open_kaishek` 运行时预验。

入库前已 rebase 到 `076daf11f592bf0ddfca9445ba995a9697925909`；相对盘点基准的两个并发提交只改日报、周报
和 preview-package 工具，没有改动本报告评分所用的原生专题或 registry 数据，故不改变上述结论与分母。
