# R01：把现有只读输入组成 ready T0

2026-10-16，source阅读点`c4992c304d196135d9590799d69ffb3c9f5510e6`。
目标是actual 1.20.0.4/Steam25734779，EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
本次没有新EXE读取、SDK、游戏、桌面、构建或主树写入；新测试全部synthetic。
既有R03研究核心6/14、业务4/11及R01未闭状态不变。

## 真正缺口与现有接点

R01来源链已在[小证据归档](evidence/episode04-r01-source-chain-20261016/README.md)保全：
R0171普通Robert key Start、历史人物1128/runtime31254、正常seed、原生合法宣战、独立war4及raise，
随后各次正常checkpoint续行。29829是开局前错误期望；1128不是游戏年份，也不是一次角色继承。
原selected独立packet和未解析人物record仍保持原限制，不能冒称已补到字段。

剩余工程缺口是把明确主体、约定统帅、完整人数/DATA、库存/容量、现金和实际战争目标合在同一暂停F，
再绑定正常保存及导演的目标/周边地点决定。所需读口均已生产存在：

| 既有接点 | 本次复用范围 |
| --- | --- |
| `mcp_server.py:3017`、`army_commander_candidates.py:94` | typed current commander及frame；候选集合partial不抹掉available当前统帅。 |
| `mcp_server.py:3042` | 完整Driver strengths，显式full profile、两个`observed_prepared`；compact MCP摘要不提供full DATA。 |
| `mcp_server.py:2003`、`war_cash_private_transport_v1.py:130` | actual treasury及actor-global来源，复用原exact-build/native-frame校验；费率不当实际付款。 |
| `war_occupation_targets_contract.py:48/76` | canonical step builder与完整独立occupation；不手拼新query词法。 |
| `g2_private_query_transport.py:18–88` | 原有paused-frame transport及queried三键；现金旧wire没有PID字段，不伪造它。 |

无需新增hook、query平台或未知callee/RVA。新模块
[episode04_ready_t0_12004.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_ready_t0_12004.py)
只组合既有strict normalizer和typed current-commander reader。

## 下一最小场景：Army18在2645停稳后的一个F

Root当前已持的状态是Army18缺11人、库存300/300，正常陆路2635→2645的D2；
这些属于`machine_id=desktop-3fevhd2-1c74096080`的已报告当前情形，不代表本包重新实读。
不用Army93作对照，因为它已在combat。继续既有受控自然日入口到2645，
以**新的实际position、空完整route、regular或sieging、非combat/retreat**判到达，不能拿预览D2当已到。
新消费者在仍moving/embarked/gathering或route非空时明确拒收T0；不补发Move/Halt。

1. Root取新的暂停snapshot F0，并用当前机器/PID/create-time/generation/episode、exact4与已批准Robert来源回执绑定。
   `source_binding`是调用者已核小回执，不是新增native字段或对历史ID的猜测；附当前director采用这条正常战役的revision。
2. `ready_t0_readonly_requests_12004(F0, army_id=18, war_id=actual_W)`返回已有只读MCP参数：
   strengths(full/两个observed_prepared)、typed commander、private cash、canonical war occupation、末尾snapshot。
   实际调用仅由Root执行；查询若换frame或revision不符，保留失败、重取只读F，不重发游戏动作。
   完整Driver原件只保存一份，多个消费者复用；每日继续用既有小读数，关键T0和桶机会才取full。
3. 先看typed current commander，再由Root明确决定保留该实际统帅并填`agreed_commander_id`。
   不自动沿用历史31254，不根据候选质量替换统帅；需要合法换将时，换完另取新F。
4. 调`evaluate_episode04_ready_t0_12004(...)`。它要求所有查询各自三键精确等于F0，
   完整DATA/ArRg覆盖与backlink、库存及容量、独立occupation和所选敌方holding都可读，
   F末尾同日期/同主体/同位置/空route及原生状态不变。public/native revision分别比较，不能要求彼此相等。
   同revision末尾snapshot只证明语义一致；实际独立请求与transport来源仍由Root小回执证明。
5. `military_t0_frame_ready=true`后，Root冻结实际`P_goal`及周边陆/海/休整地点的选择和native previews。
   2635是历史已真实战争目标，必须由本次fresh occupation和preview再确认；2645不自动视为正补给休整点。
   若讲R10休整收益，仍需已有正贡献/实际恢复准入，不能拿地点标签或getter当已恢复。
6. 仅在选择已批准且同一日期/主体仍成立时，由Root正常`ck3_save_checkpoint(expected_revision=actual_current_R)`一次。
   把实际保存body传回消费者；`normal_t0_saved`核date/actor/episode/size/SHA和ordinary/xar_off。
   它不读存档、不重hash大文件；文件存在/确切bytes仍由原materialization回执证明。

该模块不会把`military_t0_frame_ready`自动升级为R01整卡闭合。最终目标/周边地点决定与正常save仍分开，
未来现场实取并按原卡复核才可增加研究信用。R01也不要求在这里完成90日ABC结果或镜头M。

## 下一损耗窗口直接沿用什么

`loss_sampling_ready`另检查实际available/installed callback与writer journals及原生clock，
带出各自latest sequence、起始日期、原clock和source-derived下一日期/D输入。
历史overwrite如实保留，不一概抹掉后续独立新writer；也不把它们之和变成完整区间总账。
上层继续复用`army_periodic_loss_cause_evidence_12004`/`army_siege_parent_loss_evidence_12004`和现有县界消费者，
只在新实际fence/日期窗口消费完整parent与unique physical事件。
`+188`不是30日准入门；next D不能一般地storedD+1。返回的机会输入不保证下一callback成功，
更不授实际loss/ADD；Army净差、请求/预算与actual writer事实继续分列。

如果2645 fresh F显示native resupply或补员许可不合格，保留实际false，
再用既有目标preview与补员位置读口选择下一合法地点；这时缺的是具体当前输入，
不是未知EXEcallee，不能为了等一次正例无限继续35日窗口。

外置候选`r01-ready-t0-a15`拟入下一canonical source批；主树冻结期间仅相对补丁。
保留/复核按通用政策：源与资格小记录180日复核，可重建外置helper闭场48小时评估。
