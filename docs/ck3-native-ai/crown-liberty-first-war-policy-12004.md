# SDK38：王权、自由权派系、送礼预算与第一战

2026-10-17；有界source/已完成小回执审阅，0现场调用、0活Driver/SAVE/video读取、0SDK38/W/ledger修改。实际源为sdk-p38-candidate-final03/src，manifest 2c0e9d673591abf4003a4242d20188bb18136e8a49d6897c7001fa03969f85f5。当前Crown2和最早33日内0→1→2由Root通报；本包不重放升级、不补新现场查询。

## 眼下无需因王权再停机

普通policy的_NEXT_POSITIVE_SCORE只有0→1、1→2（crown_authority_policy_v1.py:12–15）；当前Crown2返回no_stock_upgrade，不会自动升3。因此现阶段无需改配置、关闭法律能力或重启SDK来避免继续升级。应先沿既有流程核验已提交的gift，继续普通游玩；本报告不是新准入或修复前置条件。

Native24/SDK38 AUTO19实际已完成响应：date53160000、episode native-31254-8d3a8440eb30、actual Game246608；派系54 liberty，power141.956/threshold80、discontent60/+10月、months_until_max4，原生dangerous=true。当前leader34973/opinion-7，wallet203.73361gold，native quote100gold/+15，matched faction+recipient+frame danger filter已在真实plan消费。结果仅submitted_verification_pending、executor_invocations1、receipt=null；不能把预计103.73361gold余额、预计opinion8、派系离开或威胁消失当实际。4个月是该帧投影，不是准确最后通牒期限。Root正在处理的publication恢复与本审计独立，本包不重发gift。

## 早期连续升级确实缺策略判断

SDK38 Crown policy、formal consumer、transport和strategy均与SDK37逐字节相同。policy:28–96仅把原版正ai_will_do映射为下一档，检查Native final CanEnact与动态费用/余额；formal:128–132没有传reserves_raw，:190–192 ready即选typed enact。没有派系危险、当前政治收益、实际选定后续项目、战备资金/威望承诺或玩家战略阶段判断。可选检查三次无操作CD不能阻止连续有操作升级；它不是策略性升权间隔。

原版00_realm_laws.txt:122–127、208–213分别给0→1、1→2 score1；_laws.info:287–293规定引擎AI在RARE_TASK_TICK检查能通过的正分法律，而非每个agent turn自动消费。Crown1/2本身的Native CanEnact/cooldown规则仍须原样尊重，不能因为33日很短便判引擎错、给Python强塞20年禁令或把component false与最终CanEnact做AND。原版存在innovation_all_things冷却豁免等条件，当前为何能两次升级不由此包推断。

风险具有明确原版依据：00_faction_modifiers.txt:2108–2129对liberty加入权重随Crown1/2/3分别加10/20/40；00_factions.txt:733–783把该modifier纳入create/join。00_faction_triggers.txt:246–268还关联最低authority的liberty建派/加入资格。王权变化又有封臣stance意见修饰；不能给所有封臣统一扣一个数字。CA1已开放partition-law変更等flag；CA2新增广succession-law、内部战争禁令与税/兵contribution。没有被本轮实际项目消费的unlock，不自动等于值得现在承担政治成本；CA2也不等于分割继承已经解决。

这证明此前升级缺少政治风险/用途权衡，不证明当前141.956%全部由升权造成。成员由旧一人变为三人、相对兵力与其他局势也可能改变；未做本包范围外的因果模拟。

## 调低能力已经存在，自动调低策略没有存在

既有注册入口（bridge/mcp_server.py:1878–1901）是：

- ck3_query_realm_law_crown_action_private_v1(expected_revision)：取得同paused frame的实际active/candidates/final CanEnact/quote/资源。
- ck3_enact_realm_law_crown_private_v1(readback,law_key,budgets,action_id)：显式选择已列的合法Crown候选。
- ck3_query_realm_law_crown_receipt_private_v1(expected_revision,submitted_request_id)：独立有效法律、资源与succession结果。

transport:218–265只要求crown_authority_前缀、该候选非active且final CanEnact=true，不限制“只能高一级”。现有Native source adapter Candidate与ResolveRealmLawCrownTarget12002同样按实际group/key/lease/final terms解析，未另加只升不降守卫。因而可复用现有MCP对当前真实合法CA1进行一次调低，无需新Native、MCP、行动路线或重启Game/SDK。但这只是已有通用执行能力，仍需实际readback确认；本包未观察当前CA1合法、未发命令、未授调低业务资格。

原版CA1 can_pass/pass_cost:77–103的冷却与prestige收费分支以当前CA0为条件，不能把0→1的升档收费或等待直接套到2→1；实际可能零prestige/合法，仍以同帧Native最终quote为准，不从文本直接提交。调低2→1会降低liberty加入权重的一项，不能保证成员即时退出或派系解散。即使再评CA0也须逐次取当前合法候选；不能跳级、改law key或把最低档建派资格等同于已观察解散。

现普通formal consumer在plan与submit两处都重新调用choose_crown_authority_upgrade_v1，故它不会自发选lower；Root如需当前调低，可合法使用已有显式MCP。调低后直接继续auto又可能尝试1→2，不能声称自动稳定于1已有实现。应保留该次原action ID、独立receipt与当前冷却/合法性；不因重新看到CA2合法便自动把调低抵销。

## 精确配置边界

源码只有一个现成对象开关driver.allow_private_realm_law_action。若既有Root受控配置路径在同一个Driver上设置False，无需改文件或重启SDK，普通formal consumer:102即不再提议Crown动作。但transport._paused:46–49同时拒绝quote、enact和receipt；它不是“只停自动提高”的专用设置。不得在Crown pending/尚需读回时关闭，也不能先关闭再声称仍能调低。此包没有执行该赋值，也未新建configuration API；是否采用同对象变更仍归现owner原有控制路径。

没有现成max_crown_level=1、只禁升权但保留全部quote/receipt、或以政治稳定自动调低的runtime参数。CLI --private-realm-law-crown-action是启动时整体启用，不是当前会话重配置MCP。直接编辑argv、cadence ledger或save不算同会话配置方案。

最小当前选择是保持现Crown2自然到顶，不插入人工干预。若Root决定通过已有MCP调低，需一并明确以后自动升级的保留/抑制安排；仅为这件事关掉全部法律能力并非首选。真正长期改进只需在原ordinary Crown新机会仲裁加入“当前实际用途/政治稳定”判断，pending/receipt照旧；它是小Python policy采用工作，无需新能力或Game重启，但本包不改冻结SDK38，也不虚称已有一个可直接设置的最高档配置。

## 礼物与宣战的最短改进顺序

此前Native22 AUTO515→531已经实扣100gold（258.10153→158.10153），opinion-8→7，旧派系54仍在、threat_resolved=false。SDK38新的danger gate在源码及离线验证中拒绝watch，此次AUTO19已真实消费同scope dangerous正例；本包没有新的watch拒绝实机回执。它解决不必要的watch礼物准入，不解决危险时的资金收益权衡。AUTO19的100gold约为当前203.73361现金49.08%，100gold reserve依然允许它，且只按cost/opinion、leader排序。预期-7+15=8低于Crown2原版注释对应的简化20意见水平，但其他join score项/更新周期未知，不能推出“必不退出”或“必失败”。

原版gift:41–51对AI有short_term_gold cutoff、首都建设优先与贪婪/和平/成年等调度；:721–743仅把不带gift modifier的派系封臣纳候选，不直接令其退出。玩家Native CanSend合法不包含全部AI花钱意愿。当前固定100gold reserve也不是第一战军费/应急储备证明。不要再建一个虚假的综合威胁分数，或把18个月maintenance自动当所有未来战费上界。

按现有能力，最小顺序是：先核验AUTO19原gift及独立派系结果，pending尚在不重发；危险仍在则把已有Native合法降权机会与再花钱相比，而非只扫描另一个未收礼成员。单次调低有可能以更低即时现金成本缓和原因，效果仍须现有独立alert读回。之后只有实际danger解除/降为watch、真实prewar force/finance/forecast等门禁均ready，才让第一场主动战争进入既有宣战链。不得为赶“第一战”移除danger或军力/预算门禁。

现war-entry行为本身合理：strategy.py:827–869区分watch/dangerous/war-handoff，:16221–16306对危险返回life-advance/NO_DECLARE；它不是“只要有派系永远不宣战”。旧AUTO515还实际有prewar V2 unsupported，这是独立缺口，不能由今天送礼或静态CanEnact填成ready。源审没有改变战意、投降策略、事件默认选项、军力门槛或当前目标。

## 移交

建议优先修复早期“合法就升”的ordinary调度，按已经选定的实际治理用途与当前政治成本决定是否升；不为演示刷法律次数，不在同一危机把降权/再升权循环化。当前Crown2不再自动升，故这项长期策略修正不阻自动游玩或publication恢复，也不触发额外重启。调低、gift完成、第一战胜利与连续30年均仍要实际结果，本报告不授任何完成。

SOURCE-AUDIT.json固定SDK38/37关系、相关原版和已闭AUTO19来源。只记录小型projection与hash，不复制完整源码或历史大件，不执行旧矩阵。sole writer可将此报告并入下一已有公共批，无须单独CI。
