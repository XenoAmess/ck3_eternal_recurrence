# G2、罗贝尔与宗教 v32：维护者度假交接

**2026-10-03 战争授权更新。** 项目所有者明确命令“取消任何的非战约束”，并要求研究战斗。原战争研究停止、nonwar-only、战争执行暂缓、战争只能交由其他维护者等现行限制全部撤销；战斗、军队、行军、围城、战争理由、宣战、防御战争、议和及相关原生 AI、只读 bridge/MCP、策略、实现和实机验收均可继续。不得仅因涉及战争再次要求授权。本文历史冻结配置的 OFF、旧尝试 RED、当时未提交动作与未实现能力保留原事实，不能继承为当前禁战规则，也不能把开放授权写成能力已经完成。继续保持罗贝尔 actor29829、episode `native-29829-2bc2d599f7f9` 的原 ordinary campaign 与自然继承线，原生 AI 研究优先、exact-build 绑定、ROOT 唯一实机/pipe/Git owner，以及最小化、无焦点、无桌面输入。当前续接身份和保存锚点以[最新接续记录](2026-10-03-g2-v33-resume.md)为准，本文较早 episode、PID 和存档仅供历史证据。

2026-10-03 收尾。用户要求“温和地做完手上的每件事，不要开始新的事情了”，本轮已停止开新工作包，完成已有聚焦测试，正常保存并关闭 CK3。本文承接 [10 月 2 日原交接](2026-10-02-g2-r11-maintainer-vacation-handoff.md)。后任应在用户明确恢复工作后执行文末接续步骤。

**先看这里。** 当前可运行版本是 v32；新补丁均未应用到生产源码、未构建或部署 v33。罗贝尔累计保存 **3845 / 36524 天**，本次续接增加 **692 天**，10 月 3 日增加 **597 天**；自然继承为 **0**。G2 **5/8**、非战争 **2/4**，机器账本 `percentage_reporting_allowed=false`，不把这些分数改写成总体完成百分比。

游戏已正常退出，原进程 PID109732、managed session43772 均结束；关闭后 `tasklist` 确认没有 CK3 进程。`faction_demand.1001` 原实例23保持未选择，后任恢复时仍需处理。没有人为跳过时间、替换人物、换开局、强制继承或执行这次派系选项。

**授权与工作方式。** 罗贝尔是当前唯一测试入口，保留其自然继承线；不新开其他书签或实机夹具。Steam 最近一次由用户确认处于离线模式；恢复前依据用户当时状态继续执行。保持最小化、不抢焦点、不操作 Steam 窗口。宗教领域的全面研究授权已经生效，撤禁工作已发布于 `6443a516`；不要再重扫旧禁令。2026-10-03 项目所有者已明确撤销全部非战约束并要求战斗研究；战争原生研究、实现、策略和实机均可继续，不再因战争再次请求授权。该 v32 冻结配置当时为 `nonwar-only`、WAR_CASH/PREWAR 关闭，保留其事实与哈希；新战争候选按实际依赖启用、构建并验收，不将历史 OFF 继承为现行规则。

多代理可在用户恢复后保持高并发。主代理负责游戏、pipe、MCP client、共享源码合并和 Git；子代理在独占外置目录完成原生研究、代码投影或聚焦测试。已有 ABI、GREEN、RED 和原生树直接复用，不重跑旧矩阵或寻找理论安全问题。

**实际版本与保存锚点。**

| 项目 | 当前值 |
| --- | --- |
| CK3 / Steam build | 1.20.0.3 / 25652598 |
| EXE SHA-256 | `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6` |
| 已发布生产源码及 native compile commit | `8cf176b436b6b0024fb591d4114b92448146181a` |
| 最近一轮已发布文档 commit | `3f80cc34b28c5fd0279495f5452c38a4a7dd1ce0`；本交接提交另见出版回执 |
| Python runtime | `artifacts/g2-maintainer-2026-10-02/resume-12003/production-source-8cf176b4` |
| actor / episode | `29829` / `native-29829-2bc2d599f7f9` |
| lifecycle | `ordinary_campaign_succession`、`xar_off`、pact absent |
| 最终 raw date / save / full history | `53236608` / `4639` / `4639` |
| environment SHA-256 | `a659ee553736c3a9429a961711411090ed6b53931a9c1a202f057b3179397486`；这不是 Git SHA |
| checkpoint | 90,951,487 bytes；`1ed74c29f7c574d390f7fd6876b2f5cb945ee4b9f148f338b89f2649ee60ca26` |
| driver-state SHA-256 | `a530dd0f247a18735076720bfabfc81599b480eba3670e45701b0eb50830f97a` |
| pipe | `\\.\pipe\xar-g2-robert-1066-seed-66f926d` |

本机状态目录为 `Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v32-20261003/state`。完整冻结副本位于 `artifacts/g2-maintainer-2026-10-02/resume-12003/vacation-handoff-20261003/frozen-v32-closed-current-pair/`；[FINAL-SAVED-PAIR.json](Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02/resume-12003/vacation-handoff-20261003/FINAL-SAVED-PAIR.json) 记录10份文件的路径、大小、哈希、正常关闭和进程检查，SHA-256 为 `afc73403b01e15f2c070ffa60a413b5eae8d9676ac2adee4f59183c880a9819e`。10份文件包含 checkpoint、完整 driver history、六个已有动作账本及原始 immutable seed 两文件。恢复应使用最新 checkpoint；原始 seed 只保留历史绑定。

**本轮已验证的结果。** v32 严格四目标构建 GREEN，实际969输入、505次新编译、502个独立 CPP、0复用，70.499512秒；完整115 flags 为63 ON/52 OFF。native manifest 为238,388 bytes，SHA `48b3dc6d93d5c224bf25a0fdd1b404874ba586030973cf8e7e019f17366ea6f2`，DLL 为8,213,504 bytes，SHA `c709e1991d221abac1a066528968c437346a65ed8e401b04195323273c98a52a`。原生构建回执在 `native-build-religion-type-tax-holy-order-v32/FINAL-INPUT-RECEIPT.json`。

罗贝尔在新 PID109732 冷恢复后保持 goal0、六账本和10 streams；后继正式窗口实际推进7天，10步为三次已有家庭结果读取加七次 life-advance，0 modal。随后100天请求只实际保存11天，被当前派系事件阻断，不能记成100天完成。前一30天请求只保存29天，状态 `turn-budget-boundary`，也不能记成30天完成。原失败、部分完成记录均保留。

v32 source 的 Official CI run `37087106124` SUCCESS，文档 `3f80cc34` 的 run `37089905100` SUCCESS。CI 不代替 native、暂停帧或完整 OODA；本交接的自动 CI 若尚未结束，不能沿用旧 run 冒充。

| 能力 | 已取得材料 | 当前边界 |
| --- | --- | --- |
| 类型 / 忏悔 | `christian_fulfillment`、Christian=true；当前运行时feature43=true；shown=false、CanTake=false、affordable=true | 固定 `tenet_confession` 许可未观测；既有信条行缺席不等于许可false |
| 教会收入 | 同暂停帧实际有效份额7.5%、配置cap25%；当前/最大0.21240/0.70804金每月；actual lessee56513 | 份额来自原生 getter，不从收入比值推算；没有改善动作或收益信用 |
| 圣骑士团 | 5组织，1军事+4非军事；军事order4最终条款可用，CanHire=false、CanAfford=true、费用106虔诚 | 原文拒绝理由含绝罚及已被雇佣；没有独立绝罚特质观测或雇佣动作；非军事行不作军事证据 |
| HoF 金钱请求 | v31金额观测故障已修复，前瞻58.33566金、shown/CanSend=false | 没有收到金钱；旧失败保留，不重新研究已修复故障 |
| 政府查询 | 两处改用语义快照；v32正式窗口实际政府context/native adapter正常返回 | 原步长1/7/30、速度3保持；计时是不同口径，不承诺提速百分比 |
| Sway | 原 `134217986` / gen8、target34333；最近目标/好感实读328/353、−8，日期53236344 | 专属Sway/blocker修正缺席、没有收益或终态；收尾四查询与保存另行归档，不把旧目标数据刷新到53236608 |
| 家庭 | Guy婚约、独立首继承人婚姻由正式consumer冷恢复保持 | 不重发原提案，不混用两套关系/联盟证据；自然继承仍0 |

以上宗教观测是只读 `production-live primitive`，不等于宗教完整行动循环。原 NW-LIFE、家庭及 Feast 子项完成合同继续保留；整体 M6 仍缺 Sway 有益材料，整体 G2 仍未完成。

**当前最优先阻点：派系独立要求。**

原生窗口实读为 `faction_demand.1001` / instance23；只显示 native option2、3。接受是 **API3**，拒绝是 **API4**，不能把 rendered0误当API1。主角与暂停日期均保持29829 / 53236608。saved scopes 的 type5标题和type25派系完整ID仍未在当前 v32 读取。

独立现成派系查询实际取得当前民粹派系33554465、leader70766、target29829、power158.154/threshold75、discontent100；成员县2102、2111、2115均直接由罗贝尔持有。这个实际集合与窗口leader相符，但 saved faction FullRef 尚未实读，不能声称已精确关联。县意见新 getter 已有非空实机样本，不增加治理收益信用。

接受选项调用 `successful_popular_revolt_outcome_effect`。普通分支会从成员县扩大到相应法理公国内属于罗贝尔 realm 的县，可能转移持有公国、按王国划分独立主体，并在控制法理县超过50%时篡夺王国。因此三个成员县只构成损失下界。拒绝选项明确调用 `faction_start_war`；WAR flag关闭不会改变原版脚本效果。上一日已读政府为feudal，但它不是事件同帧的 `government_allows=state_faith` 最终判定。

[原生事件树](../ck3-native-ai/ck3-1.20.0.3-faction-demand1001-populist.md) 已冻结完整effects、immediate/after、直接依赖与AI权重。后任先补 type5/type25 与实际割让影响范围，再设计最小策略。当前战争研究与执行已获 2026-10-03 所有者全面授权；补真实军事观测、研究防御与战斗路径，再按当前可执行策略处理事件，无需仅因拒绝会开战另请授权。该 v32 收尾当时没有代选任一分支，此事实保持。

**收尾补丁与研究包。**

本批 source patch 没有应用到生产树。可恢复的压缩原补丁、交付回执与完整哈希保存于 [补丁索引](2026-10-03-g2-religion-v32-packets/index.json)；大型 wire、日志、EXE和存档留在本机 artifacts。压缩补丁解压后按索引里的原始SHA复用。它们是既有在手工作成果，后任无需重做已通过聚焦验证。

| 包 | 已完成 | 剩余 |
| --- | --- | --- |
| type5标题 scope | 5叶 native补丁；production reader→serializer唯一case GREEN，原harness RED保留 | Python `_event_scope` 的 type5 shape/null reason未接；与type25逐hunk合并，组合DLL及暂停帧 |
| type25派系 scope | FullFactionID保generation，production serializer→Python三帧 GREEN | 实际saved faction ID未采；与type5共同字段手工合并，保持旧aggregate前三项 |
| 固定忏悔许可 | 4 unique文件；native/Python各1case，8语义场景 GREEN，首链接RED保留 | 现宗教context共享mailbox/CMake/transport未开始；绑定同actualContext与actor |
| 奉献/德性/贫穷誓愿 | 13文件含三叶与外置已有查询接线；55 checks/2cases及生产Python两wire GREEN | 严格组合构建与罗贝尔实读；没有决议动作或净收益 |
| 县改宗 | component6路径及glue9路径已冻结；7case/28断言/7JSON，完整native wire与注册MCP链 GREEN | component先于glue；组合DLL与暂停帧；目标Rite/Faith/意见价值及typed动作后置 |
| 圣骑士团所选地产 | 6 unique native文件；三个固定决议/三个选中标题联合case GREEN | CMake、reader callback、目标MCP/normalizer未开始；fixture报价不是实机报价 |
| 朝圣路线/ETA | 内部两叶与唯一reader/serializer case GREEN | 候选资格/活动报价组件的共享查询接线；原生Date不按raw差自行换算天数 |
| 朝圣候选/活动报价 | candidate factory2文件、owned config/quote2文件；已有组合case已收口，见索引最终回执 | CMake/mailbox/transport、暂停帧；activity十资源费不等于整个旅程费或CanStart |
| 全旅程费用/返回安排 | 截止收尾的只读原生证据已冻结 | service/options inclusion及phase/return schedule仍research；不把stock三个月当全程ETA |
| 绝罚/悔罪 | 精确stock/native树与41段证据，正确请求key `declaration_of_repentance_interaction` | 独立绝罚trait、当前recipient/最终条款/PAM route均未实读；没有实现或解除动作 |
| 实际割让范围 | 现查询清单、subrealm/title registry与原生接口研究已封存 | GetDeJureLiege与完整seized title范围未实现；已有成员行不代表完整损失 |

没有开始 v33 部署。type5/type25、宗教mailbox、CMake、Python common文件是后任合并点，不要用一包投影整文件覆盖另一包。县改宗的doc/glue基线是先应用组件包后的版本；其他主体以immutable `8cf176b4` 为基线。朝圣 generic非single-location计数入口尚未闭合，single-location只跳总phase gate，仍保留同province重复/上限判定。

**位置与出版。** 实际施工树是 `Z:/ck3_mod_rewrite/.task-tmp/g2dlv`；原工作区已有脏改动，保持现场，不reset/stash/clean或广泛git add。ROOT脚本、正式有限runner和已发布回执均在 `artifacts/g2-maintainer-2026-10-02/resume-12003/`。使用 `tools/.venv/Scripts/python.exe`，当前环境已验证 `cmd.exe`、`login:false`。正式接受流程仍遵守 [testing-workflow](../testing-workflow.md)。

最新发布回执为 `day03-v32-religion-3834-progress-published.json`；本交接回执为 `day03-v32-vacation-handoff-published.json`。日/周滚动报告更新到最终3845与停机状态，但这不是午夜正式收口，不能倒填为00:00计划。保留其他并行任务的war/video文档。提交只选本次拥有的文件；从实际public baseline生成diff再三方合并到最新origin，避免旧owned分支的报告差异覆盖上游。正常push，任务不要求发布工坊或翻译其他语言。

**后任恢复步骤。**

1. 先读本交接、`AGENTS.md`、[原生AI索引](../ck3-native-ai/README.md)、[统一路线图](../autonomous-agent-progress/goal-and-roadmap.md)和补丁索引；报当前3845、G2 5/8、NW2/4、0自然继承及停机状态。
2. 按用户当时的游戏与窗口授权决定何时恢复，保持罗贝尔唯一起点、离线/minimized/no-focus约束。引用最新4639完整pair，不回放4031或原始seed，不重发任何已有动作。
3. 优先使派系事件所需观测可用：合 type5/type25 + Python type5，再补真实割让范围的最小只读口。现成 `ck3_query_player_faction_alerts_v1(expected_revision)`允许当前暂停modal读取；原失败/unknown记录保留。
4. 宗教可同时后台推进：已有固定许可、奉献、县改宗、所选地产、朝圣组件按依赖合并。复用已有唯一聚焦证据；只有新增共享接线需要对应的必要验证。冻结实际组合source与exact build，再做严格四目标构建和官方prepare/verify/rebind/preflight。
5. 由唯一主代理最小化启动管理进程，做新PID冷恢复、原账本消费和必要实际暂停查询；epoch、public/native revision、source/native/environment分别记录。只有当前决策所需字段真正解锁，才恢复策略与正常时间推进。
6. 按已开放的战争授权研究当前派系拒绝分支所需战斗、军事观测与实际执行路径，完成当前事件策略后继续原Sway的有益材料、M7自然继承及长期正常游玩。更新日报/周报、原生专题、机器账本；完成每包即commit+正常push，不把ACK、fixture或只读primitive写成完整游戏循环。

可直接使用的接续 prompt：

> 接手 `docs/handover/2026-10-03-g2-religion-v32-maintainer-vacation-handoff.md`。本轮前任已温和收尾并停止，不要假定v33存在或新补丁已进生产。先报告3845保存天、4639完整pair、G2 5/8、NW2/4和未选择的faction_demand.1001/23。用户明确恢复后，保持罗贝尔唯一入口、最小化不抢焦点，主代理独占实机/共享合并/Git，各子代理在独占投影高并发完成实际工作。优先补齐type5/type25与真实割让范围，避免盲割让或开战；同时复用封存宗教组件及测试，补共享接线、严格组合构建与新PID暂停帧观测，再恢复有价值的策略和原长期游玩目标。宗教全面授权持续有效；2026-10-03全部非战约束已撤销，研究战斗并继续战争相关观测、实现、策略和实机，不因战争再问权限。不得重扫宗教禁令、重审已修复故障、重跑旧矩阵或新增理论安全门禁。按原生树先研究后策略；保存失败、保持已有动作不重发，逐包更新报告、commit并正常push。
