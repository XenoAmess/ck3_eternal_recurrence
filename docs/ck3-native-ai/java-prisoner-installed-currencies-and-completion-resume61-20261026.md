# 当前安装囚犯交互与 Java ordinary 完成条件

machine_id: `xenoamess-full-tower-eb9d2c1186`；读取时间 `2026-10-25T23:01:37Z`。
范围：安装文本、现有 Java 源码及冻结 Native source60 的静态对照。没有启动 JVM、编译、测试、采样、连接 pipe 或操作 CK3。

当前 Java ordinary 的赎金动作覆盖 `gold/current_gold`，释放动作保留当前实际查询到的十三项条款意图。
原生 `CanSend`、接收方回答及最终上下文验证已经在这条链中；额外货币及条款收益仍缺相应选择和独立后态消费者。
释放回执的 `material_result=true` 当前证明其所检查的自由状态，字段同时保留
`release_causation_observed=false`、`command_costs_verified=false`。它不授予转换信仰、誓愿、招募或财产转移的完成信用。

## 来源和复用边界

沿用 [赎金动作迁移](prisoner-ransom-action-1.20.0.4-migration.md)、
[正式释放入口](prisoner-release-formal-service-12004.md)、
[现有原生树](prisoner-disposition-native-ai-tree-12003.md) 和
[独立释放结果](prisoner-release-independent-receipt-12004.md)。这些专题已有的 ABI、旧测试与历史实机结论继续保留原范围。
本次新增的是当前 Java caller/consumer 对照，不重复旧 EXE 研究。

安装目录为 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game`。
正式安装见证 `resume61/formal_release/INSTALLATION-WITNESS01.json` 记录 Crozier `1.20.0.4`、Steam build `25734779`，
复用 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 的元数据一致性。
本岗没有重新读取 EXE，也没有核已加载 DLL、脚本覆盖优先级或在途交互实例。

本次实际读回：

| 安装文件 | 字节 | SHA-256 |
|---|---:|---|
| `common/character_interactions/00_prison_interactions.txt` | 222958 | `1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5` |
| `common/scripted_effects/00_prison_effects.txt` | 73376 | `ea8bb72426246692bf1f310ae7eb83715ae1b7314d046e3660df66443d486030` |
| `common/scripted_triggers/00_diarchy_scripted_triggers.txt` | 26300 | `3995f62fe332f98ccecd39abf70a2a2574fbfb18c86f5d5d3c02a367fda0607a` |
| `common/script_values/00_basic_values.txt` | 50566 | `c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef` |
| `common/script_values/00_interaction_values.txt` | 23158 | `52a7cf8ef212c835bfc5bc5ce049af2e33d7586eb9d477343e8eedacf58ebd66` |
| `common/scripted_effects/pam_effects.txt` | 369911 | `fc4c77974a7844c31c1271dcc2ace24b17906620a832658919aa281e42a2b94f` |

交互文件与旧 pin 相同。实际安装的赎金 effect 在 `00_prison_effects.txt:232` 还调用
`pam_philanthropia_ransom_payer_effect`；该 helper 在 `pam_effects.txt:457-473` 依据个人教义为 payer 增加虔诚和精神满足。
释放交互 `5337` 也调用 `tenet_benevolent_governance_clemency_effect`。
这些是本次安装文本中的真实调用；单一交互文件的旧 pin 不能证明其整个依赖闭包的原始发行来源或当前加载状态。
本记录因此分别保留“安装文本已读”和“已加载效果未知”，不据目录名称追认纯原版运行资格。

完整十四份证据路径和当前 Java/native 文件 SHA 在
`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m2_research/prisoner_ransom_release17-plan.json`。
由同一份记录生成的 [图与边表](java-prisoner-installed-currencies-and-completion-resume61-20261026-graph.md) 区分原生边和我方选择规则。

## 玩家合法性、角色与接受时间

`ransom_interaction:1886` 是向外索要赎金。原 `recipient` 被保存成 `secondary_recipient` 囚犯；
非统治者若有 liege，则将 liege 放到 `recipient` 作为 payer（`1893-1905`）。
显示条件要求囚犯仍由 `puppet_or_actor` 关押，且 actor 与 payer 不同（`1922-1928`）。
`1930-1951` 另查正在受刑、旧摄政权力和正在清洗；摄政 helper 的 `376-393` 依据实际 prisoner、liege 和 diarch 关系分支。
释放交互 `4312-4347` 使用 actor→recipient 囚犯角色，同样检查这三类合法性条件。

这些条件已经通过原生上下文总结果进入现有查询和最终提交。Java 没有理由再靠自行推导的字段复刻一套合法性引擎。
本次也没有把某个未投影的细分 flag 写成当前动作必缺的新前置条件。

赎金 `on_accept:1963-2075` 在接受时重新确认仍由本 jailer 关押，设置 prisoner/payer/imprisoner 角色，
处理 haggler，并将 `current_gold`/`extortionate_current_gold` 的 payer 当前金币保存为 `ransom_saved_gold_value`。
`current_gold_value` 的实际定义是 `gold` 后 `floor=yes`（`00_basic_values:458-461`）。
`normal_ransom_cost_value:187-241` 还受文化、财富、难度与 haggler 因子影响，`increased:280-285` 在其上乘 `1.5`。
暂停时报价不能授予未来实际转账金额，单凭头衔等级也不能重建这些原生报价。

## 九个赎金选项与当前覆盖

选项顺序来自同一安装交互，Java `RansomOptionMask12004` 也固定 authored count `9`。

| 序号/选项 | 安装显示或有效条件 | 接受后的直接 effect | 当前 Java ordinary |
|---|---|---|---|
| 0 `extortionate_gold` | jailer 王朝 perk，payer 足够 increased cost | payer `pay_short_term_gold`→jailer，并给 jailer prestige | 不选择 |
| 1 `extortionate_current_gold` | 同 perk，payer 不够 increased cost 且 gold≥1 | 接受时已保存 gold→jailer，另 prestige | 不选择 |
| 2 `gold` | 无该 perk，payer 足够 normal cost | normal cost→jailer | 已有 action/quote 和独立 gold 后态 |
| 3 `current_gold` | 无该 perk，1≤payer gold<normal cost | 接受时保存的 gold→jailer | 已有 action/quote，后态只要求正实际 gain |
| 4 `favor` | mass action 排除；jailer 当前可对 payer 加 favor hook | jailer 获 payer 的 favor hook；特定角色另 opinion | 不选择 |
| 5 `influence_send_option` | 非 mass，双方 influence 政体、同顶层领域；actor influence≥medium | payer 减 influence，jailer 增 influence | 不选择 |
| 6 `herd_send_option` | actor 人类、双方 herd 政体和 domicile，payer herd 足够 | payer `pay_herd`→jailer，值取 prisoner.ransom_herd_value | 不选择 |
| 7 `current_herd` | 相同角色/政体入口但 payer herd 不够 | payer 当前 domicile.herd→jailer | 不选择 |
| 8 `invalid` | mass ransom 的最后显式失败项 | 交互级 invalid 合法性失败 | 诊断位置，非动作 |

显示/有效条件在 `2097-2228`、`2551-2558`；effects 在 `00_prison_effects:136-233`。
尤其 influence 的显示条件检查 actor 余额，而实际支付分支修改 payer 和 jailer；应保留这两个脚本 scope 的区别，不能直接按按钮文字互换。
同一 effect 还处理 payer/囚犯之间的 opinion、indebted hook 等；这些不是 jailer 收款的替代后态。
`pay_short_term_gold` 的引擎内部 treasury/gold gateway 继续复用 Loan 岗的已有研究边界；本次只闭合脚本调用，不追认该 effect 的完整引擎注册。

## 十三个释放条款与“已完成”的范围

安装顺序为 demand_conversion、renounce_claims、banish、gain_hook、take_vows、change_prison、make_puppet、become_executioner、
recruit、disfigure、blind、castrate、demand_admin；`send_options_exclusive=no`（`5984`），组合必须来自当前真实 preview 和最终 CanSend。
`auto_accept:5986-5997` 对其中列出的约束项逐项检查；未自动接受时，原生 recipient answer 仍是不同的输入，不能拿 sender 愿意释放代替。

`on_accept:4358-4371` 仅在仍由 actor 关押时执行，且 disfigure/blind/castrate 走后续事件释放。
disfigure 的 `4840-4863` 明确设置六个月受刑 flag 并排 `prison.1030` 一天后事件。
其他条款分别有信仰、claims、hook、court/任职、traits/government 或财产 effects；例如 `4453/4510` 的 banish 会在具体条件下转金币，
`4578-4604` 只移除受该分支过滤的 claims，`4615-4618` 才是 favor hook。
无要求分支 `5005-5030` 才写 `released_from_prison` opinion。带要求的释放不保证出现这个命名关系修正。

当前 `NativePrisonerEffects12004:65-85` 的释放完成消费者要求 retained full-ID target 为 `Free`；
`Dead` 或 `HeldByOther` 进入非 applied 的终态，仍在押/unavailable 保留 pending。
可选 `material:136-159` 分开比较 named modifier 与 total opinion，并保留 causation=false。
因此，当前动作可以报告自由状态被独立观察到；条款效果、实际 on-send 成本、延迟事件完成与因果归属仍需各自实际结果，不能通过自由状态字段补写。

## 当前 Java 的真实调用链与具体余项

`PrisonersRuntimeInstaller:68-100` 安装现有 native query family、准备器、ordinary policies 和 actions，
`205-209` 把同一 runtime 的 snapshots/reads/collection/archive 交给 `NativePrisonerEffects12004`。
`catalog:240-246` 检查当前 pinned stock 字节，构造本身不代表已部署或运行。

`PrisonerCollector12004.collectRansom` 对完整返回 collection 的每个 ordinal 发真实查询；
`collectRelease/retainedReleaseEntries` 消费同帧 history 中每个 ordinal 的最新实际条款，并在选中后刷新原 intent。
`PrisonerOrdinaryPolicy12004:65-115` 保持已有 positive ransom、complete war-retention 与原计划优先级。
`PrisonerRansomFormalPolicy12004:189-195` 的同王朝、自己子女、头衔层级等裁剪是现有我方候选范围；这不等于原生完整可操作全集或 NPC 跨交互比较器。

冻结 source60 的 `ck3_12004_prisoner_ransom_action.cpp:82-202` 仅接受 gold/current，重查同 payer/prisoner/amount/answer，
选择 native option 2/3，最终 `context.validate` 后只返回 `submitted_verification_pending`。
release counterpart `136-239` 复查十三项 mask、CanSend、answer 和十项 on-send costs，再验证当前上下文并入原生队列。
这些是已读源码调用，不代表当前二进制已加载该实现。

当前赎金独立后态 `NativePrisonerEffects12004:86-109,173-177` 要求完整 collection 不再含该囚犯，加实际 jailer 钱包收益：
gold 为 gain≥quote，current_gold 为 gain>0。它没有观察 payer 的扣款、herd/influence/hook、额外 prestige/教义效果或 payment 因果。
这些是明确的覆盖边界；本次没有发现可由真实当前生产路径复现的新错误，也没有因此加防护或推翻现有 gold 回执合同。

可施工的后继应先选择具体真实业务：新增某一种货币时，同步原生当前 quote/mask/最终 submit、Java typed choice、
序列化以及该货币的独立 payer/jailer/custody 后态；新增某个 negotiated 收益时，先补其实际结果 producer，再让策略消费。
没有相应输入时继续保留现有动作范围和明确的 UNKNOWN/pending，不能把新研究作为首场运行门禁。

`native_research_plan.py check` 实际 exit0：十四个证据文件，五条静态边、一条我方策略边、一条未知边。
两项业务 case 均为 pending；没有 live-confirmed 边。
plan SHA `631c7e39d8b0f5c6a87887be0f9f1e75b019d092c9546731d39020766d8c5ce4`。
