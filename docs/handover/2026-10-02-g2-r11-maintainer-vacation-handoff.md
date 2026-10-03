# 2026-10-02 G2／CK3 1.20.0.2 维护者休假交接

**2026-10-03 战争授权更新。** 项目所有者明确命令“取消任何的非战约束”，并要求研究战斗。原战争研究停止、nonwar-only、战争执行暂缓、战争只能交由其他维护者等现行限制全部撤销；战斗、军队、行军、围城、战争理由、宣战、防御战争、议和及相关原生 AI、只读 bridge/MCP、策略、实现和实机验收均可继续。不得仅因涉及战争再次要求授权。本文历史冻结配置的 OFF、旧尝试 RED、当时未提交动作与未实现能力保留原事实，不能继承为当前禁战规则，也不能把开放授权写成能力已经完成。继续保持罗贝尔 actor29829、episode `native-29829-2bc2d599f7f9` 的原 ordinary campaign 与自然继承线，原生 AI 研究优先、exact-build 绑定、ROOT 唯一实机/pipe/Git owner，以及最小化、无焦点、无桌面输入。当前续接身份和保存锚点以[最新接续记录](2026-10-03-g2-v33-resume.md)为准，本文较早 episode、PID 和存档仅供历史证据。

2026-10-02 授权更新：项目所有者已全面开放 faith/religion、rite、doctrine、tenet、fervor、改宗、宗教改革、clergy、holy order、圣战与大圣战的深入研究与实现。下列冻结记录中的旧宗教暂缓仅保留当时事实，已全部撤销；详见[当前授权](../../AGENTS.md)。开放不自动提升能力等级；2026-10-03 战争研究停止和执行暂缓已撤销。罗贝尔唯一测试入口、玩家限定与最小化后台操作继续有效，历史冻结 OFF 不作为当前禁战规则。

后续施工入口：先沿[宗教整合](../ck3-native-ai/ck3-1.20.0.2-religion-integration.md)、[教义与Tenet](../ck3-native-ai/religion_doctrine12002_overview.md)和[改革](../ck3-native-ai/religion-reform12002-overview.md)的原生树与已有只读查询补齐当前exact-build输入；自然宗教事件按真实选项、作用域与效果接回事件消费者。Holy order等未闭合分支继续定位原生资格、成本、对象状态及结果查询，先交付只读bridge/MCP，再据罗贝尔paused材料设计和验证策略；旧版实机证据不自动继承。

实际收口时间：2026-10-02 01:10:05（Asia/Shanghai）。项目所有者明确要求“温和地完成手上的每件工作，不要再开启新的工作”。已结束当前批次、保存完整现场、正常退出自有 CK3；仅收口在途源包、实际 CI 文档故障、报告与交接。以下待办供下一位维护者接手，本轮没有启动。

## 先看结论

- **G2 仍为 3/8**：M0/M1/M3 complete，M2/M4/M5/M6/M7 in_progress。Robert **3153/36524** 持久日不变。
- 独立 1.20 rogue episode（actor29829）R10 实际推进31日、R11推进9日，合计 **40日**，不是 Robert、百年或双种子进度。
- CA1 已闭合一次真实动作→独立扣款／生效／继承状态→次日 checkpoint→新进程冷恢复的窄 **production-live loop**。M6 仍有其它必需项。
- R11 正式 nonwar loop 独立验证了 `serve_the_crown_perk`，随后在第11次回合的 campaign-root 查询抛错；**整批 RED**，已返回10轮与真实9日保留。最后保存成功，最新配对 **h165／full165**。
- 自有 PID97312 于 **2026-10-02 00:28:41 CST** 正常退出，supervisor exit0，游戏／屏幕资源已释放。本次交接不保持后台游戏或测试循环。

## 现行授权与分工

用户已明确恢复宗教研究，并于2026-10-02再次授权宗教领域全面深入研究与实现；旧宗教暂缓、两项窄例外和holy order暂缓全部撤销。2026-10-03 项目所有者已撤销**停止战争相关研究**和全部非战执行限制，战争原生研究、实现、策略与实机可继续，不再要求战争领域再授权。禁止抢占 Steam focus、罗贝尔唯一测试入口和玩家限定继续有效；旧战争执行开关只描述该 R11 冻结配置。未来获准继续实机时使用已有 managed-session 的直接 `ck3.exe` 启动，禁止旧 `steam_focus.py` 或 Steam 界面启动路径。

64并行用于互不冲突的文件／逆向／编译工作，游戏、pipe、UI、进程与 Git 由一个协调者串行操作。共享源路径明确指定单一 owner；不要把64并行解释为64个游戏进程。当前休假指令优先，不再派生新工作。右下角 Toast 的持续清理授权仍有效。

## 唯一最新接续现场

以下简称 **B** 为 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01`。B 里旧 h98/h134/h139 和失败 attempt 都是历史证据，最新接续以本节 h165 为准。

| 项目 | 最新值 |
| --- | --- |
| 游戏 | CK3 1.20.0.2 Crozier／Steam25588574 |
| EXE | `Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` |
| EXE SHA-256 | `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D` |
| 完整 state | `Z:/ck3_mod_rewrite_process_assets/g2-12002-nonwar-r11-20261001/state` |
| actor／episode | `29829`／`native-29829-3f80e147d033` |
| lifecycle | `rogue_one_life`／`xar_on`，不是 ordinary Robert |
| environment SHA-256 | `2409c8b23978a17117796e41d453f156529a56cfd3d9f5b7903af7d30e351861` |
| 日期／save anchor | raw `53170320`／h165 |
| checkpoint | `state/profile/save games/xar_checkpoint.ck3`，70962150B |
| checkpoint SHA-256 | `ee4e0f2b7d8a8972a256e2b51b75f6655a26a8e383305732cac5f39c1cad05f7` |
| driver | `state/native-session/driver-state.json`，format2，完整history165，848969B |
| driver SHA-256 | `7193eb172c71eb0c4d05f0e4db73ff257b7f820664d11fb84f085cba3c7d5b23` |
| 家庭账本 | `state/first-heir-marriage-formal-v1.json`，4660B |
| 家庭账本 SHA-256 | `efa66451bc784e810e981fd8f7eb482f568364525f930f41ea44a61b0709a9ae` |
| 冻结 Python runtime | `Z:/ck3_mod_rewrite/.task-tmp/g2live11fix`，`9ce5e00a61ee9eb8db391cebe9b37b30edbb5419` |

[最终配对回执](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/r11-vacation-closeout/FINAL-CONTINUATION-RECEIPT.json) SHA-256 **`eb833d4513c1520600ce187fe3ed9f2b42bacc6e02bb098a5aeca181fc00e9dd`**。同目录的 `final-xar_checkpoint.ck3`、`final-driver-state.json` 和家庭账本为不改变原件的最终副本；全部其它 sidecar 保留在完整 state 中。最后保存帧 paused/map ready，没有待处理自然事件；技能 applied receipt 已被后续 turn 消费，不能重发技能、CA1或旧婚约。

停止请求／响应在 `B/live-run-11/root-stop-r11-20261001T162841Z-{request,response}.json`。这证明 root 自有进程正常停止，不涉及结束用户其它进程。

### 原生候选与启动文件

R11 最终原生 manifest：`B/nonwar-integration-r11/integration-build-manifest.json`，SHA-256 `813e14f7c8bd6150effb45621bba3965d1fa72b020df5df6d757182bdaa749a7`；**61 ON／4 OFF，默认0 ON**，双 DLL/injector 构建 GREEN（jobs64），468项实际 compiler inputs 已提交。编译输入与提交 HEAD 分别按 manifest 记账，不能只用较早 build_source_head 宣称所有新源已经提交。

- candidate DLL：`05b4d5ced153fc04a35d211c6d8b6ea42b7a5ed69c4fb654708201627200253d`。
- candidate injector：`b31c4e2bdefa1e4bafc4410dd8b6c7094345b816380fddf84641084586e3a9cb`。
- 新增 `permitted_executor_sway_outcome_opinion12002` 只开放 `query-sway-outcome-opinion-v1-private`，不是新的动作／事件入口。

正式 MCP 计划在 `B/r11-file-only/prepared/MCP-NONWAR-OODA-NEXT-PLAN.json`，SHA-256 `25c75d9778529858c2c318645c1079b5bf6c92ac5fa2d90e8008d3ec7867c95f`：37项只读加明确 nonwar/Council 消费。该 R11 历史计划的 `--nonwar-only` 属于 MCP/native-auto-run，native-session 不接受这个参数；当前战争候选撤销该非战限制并记录实际 argv，不修改旧计划哈希或把历史输入改称已启用。

**原 `prepared/NEXT-LIVE-PHASES.json` 仍绑定初始 h139。** 本次生成了 `B/r11-vacation-closeout/NEXT-LIVE-PHASES-LATEST-H165.json`，只把原阶段 argv 的预期 save／driver pins 指向最新配对，未执行。下一维护者先读该文件；若要采用更晚源码，使用已有官方 profile/rebind 流程保留 full165 与账本，再做当次 preflight/allocator。不要重放 hardcoded h139 的旧准备器，也不要直接调用仍引用旧计划的 `run_live_phase_r11.py`。

`g2live11`／6a91fa6 是首次 Feast 修复的历史 runtime，已被 `g2live11fix`／9ce5e00 取代。晚于9ce的 M2压力 policy 已在源中提交，**没有热改进本次实机 runtime**。

## 已完成的在途业务与真实故障

### R10：自然31日和摘要故障

`B/root-nonwar-live-next/root-normal-advance-r10-01` 实际自然推进30日（raw53169360→53170080）并保存h134。尾部摘要读错 `state/driver-state.json`，原 exit1 保留；helper 仅改用现有 `driver._native_driver_state_path()`。独立恢复证据 `actual-end-recovery-r10-01/ACTUAL-END-RECOVERY.json` SHA-256 `a7b04f674445de42ae664a9da70e561ee6aec357fc96517f833cb3edc07fd353`，未重跑30日。

后续 CA1 独立动作及正常1日推进形成h139。默认1/7/30时间策略未改，没有强制事件、控制台或战争 planner。

### CA1：已完整闭合一次法律动作

原生 AI 权重1，价值为撤销／收回权利及CA2前序，**不改善当前partition，不宣称即时收入**。原版 CA laws 为 cumulative；CA1 baron minor layer−30 不是减掉旧层。

仅提交一次 `m6-law-ca1-29829-53169360-20261001`（ID保留旧日期标签，实际执行raw53170080）。fresh cost223prestige，prestige raw214460700→192160700，扣22300000；其它5资源和完整10头衔继承集合／primary2141不变。

首次回执 `native_law_crown_action_frame_unavailable` RED 保存在 `B/m6-law-live-next/runtime/enact-20261001T154045Z`。独立 source确认已生效后，仅同ID只读恢复；`receipt-20261001T154536Z/result.json` 为 enacted，effective/resources/succession_verified=true。次日 h139 保存见 `next-checkpoint-20261001T154846Z`。

R11新PID恢复后独立比较原五资源、full10继承和法律，全部通过。`B/m6-law-live-next/recovery/cold-source-material-proof.json` SHA-256 `669f2bd318fefd251e22f74588313b085651c1011d0bc846ccd38d67dcea5579`；material manifest SHA-256 `a20b4c6a44f7b76bb2d1901cb30ad7b563fd0095de207fa567a370f4ffc6c954`。见[法律专题](../ck3-native-ai/ck3-1.20.0.2-ca1-production-outcome-2026-10-01.md)。这是 M6 法律子项结果，不是整个 M6。

### R11：冷查询首批 RED，后来同进程 fresh GREEN

首次 `B/targeted-sdk-r11/r11-cold-law-and-sway-material-20261001T160813Z` 的051 LAW／054 Sway opinion／057 completion均RED，058 snapshot pump ready，executor starts/executed为0。该包没有保留 raw native command_result，无法精确归因 callback 或整帧变化。

同PID、无代码／DLL修改、无重启的 fresh三查询随后全部GREEN：`r11-cold-law-and-sway-material-20261001T161908Z` 的003 LAW／006 dedicated opinion／009 completion。中央诊断 `B/r11-cold-shared-diagnostic/result.json` SHA-256 `be8d4a10a881393d576f7bd33551cbc5dc20c5c672e9dfff605e778fdb2c2323`。首批RED保留，未据此新增重试框架或宣称 provider bug。

### Sway：真实观测，尚无终态或收益

最后已证明进度为raw53170080的 **42/350**（原12/355），目标33433，Scheme full50331723/gen3，CanContinue=true，成功率输入72%。三终态记录器已挂载但记录为空；phase目标不等于整个方案终态，余308条件单位不等于保证308天。R11后9日没有重新读进度，不能线性补成52。

R11 raw53170104、native6 独立材料读到总好感−18；`scheme_sway_opinion`／`sway_blocker_opinion` 均 **observed=true／present=false／value=null**，是已观测合法缺席，不是读失败或Sway成功零收益。`B/m4-intervention-live-next/r11-material-live-baseline.json` SHA-256 `5243cf3cb2f4269c8c8ef2a6d99d736c0212046f66fee20039f48c5dddf367f6`。不能计M4干预完成或M6scheme完成。

当前33433是直接封臣及最佳steward（15，替代最高11），保留 **NO_CHANGE**。不要为凑验收替换成更差人选。

### 正式 nonwar：技能实际生效、9日、查询失败

root external helper 为 `B/root-nonwar-live-next/run_formal_nonwar.py`，SHA-256 `24c22a10ce65fcfb2ae854bc7f4e6d25fb7a270de2f68228d103bfcab612bb50`，使用现有生产 `plan_nonwar_turn/auto_nonwar_turn`，显式 nonwar，不调用旧全域战争 planner。

`formal-r11-01` 在raw53170104、可用点1／used13／martial_authority_focus时仅提交一次 `serve_the_crown_perk`，action `life-perk-e7d01f83222c45c0952ef2938638dfa2`。选择价值是既有策略中的feudal county control +0.3。

`formal-r11-02` 的第1轮正常1日；第2轮独立 receipt为 **applied／post_target_perk_owned=true／postcondition_verified=true**（raw53170128）；第3轮消费结果并继续正常推进，没有重发。总10轮返回、9真实日，到raw53170320。

第11次调用 `_prepare_succession_transition_v1 → query_turn_bundle → campaign_root_context` 抛 `_NativeCommandRejectedError: native gameplay step failed: application-main typed query failed or its snapshot changed`。**整批 exit1／RED，原目标30日／64轮没有完成。** 原 sent-packets／received command results／before-submit／snapshots／trace 都保留在 `formal-r11-02`。没有新的自然modal，最后常规advance已暂停。

`formal-r11-final-checkpoint` 仅执行最终checkpoint成功，形成full165/h165。这个技能还没有新PID cold证明，不能借CA1cold替代。休假本轮不再调查该新查询RED或重启游戏；下一维护者从最新暂停配对与原command结果做窄复现，先读当前campaign root，避免重复提交已生效动作。

### Feast：修复实际 envelope，完整生命周期待接手

R10实际 Open 成功、stage1／selectedFeast／widget visible+attached；旧 Python 要求新版8-key包没有的 `same_frame` 而误报 `RED:opened`。第一次修复的fixture补了实际为null的source_frame EXE SHA，原错误包保留，就绪判断已撤回。

最终fix复用 `private_native_provenance(after)` 读取真实 `hello.expected_ck3_sha256/ck3_build_match`，原始 before／after／wire 不改，唯一受影响caseGREEN。已冻结9ce runtime。`B/m6-feast-live-next/feast_live_next.py`／`feast_pipeline.py` 的stdout压缩到1643B，1243422B原报告保留。

**R11没有运行新的Feast qualify／start／结束矩阵。** 缺 fresh CanStart／cost／budget／Start／terminal，冷恢复不能把旧stage1当当前stage。当前一场战争可能影响既有预算reserve；empty hosted 本身不证明合法hold。下次先fresh资格／预算查询，见外部Feast runbook与[实施账本](../autonomous-agent-progress/g2-offline-implementation-2026-10-01.md)。

## 八项合同与未完成入口

权威合同在[机器索引](../autonomous-agent-progress/g2-requirements-v1.json)与[路线图](../autonomous-agent-progress/goal-and-roadmap.md)，保留原 visible_outcome，不因本次源码／窄live降标准。

| 项目 | 状态 | 玩家可见验收／交接缺口 |
| --- | --- | --- |
| M0 三出口比较 | complete（历史） | 同一暂停帧比较继续／白和／投降，独立战后和cold；复用历史；2026-10-03 战争研究已开放，按新实际任务继续 |
| M1 实体和turn bundle | complete（历史） | ruler／title／capital／liege／vassals／neighbor及最小警报；迁移新查询不能自动重授全部广矩阵 |
| M2 自然事件 | in_progress | 三个真实自然事件，含两个多选，验证材料变化；本次没有新增该矩阵。晚提交.1007/.0030原生stress条件metadata在source static-ready，未进入9ce live |
| M3 继承和生存 | complete（历史） | 自然死亡前预测、核对真实继承、接任后继续；这不替代M7广资格 |
| M4 和平治理 | in_progress | 同一两游戏年窗口：建设、合法Council重派、真实封臣／派系干预；现建设报价已观测，旧private建设loop有效，当前seed有war／army守卫，最佳Council不应降级，Sway收益未出现 |
| M5 家庭／外交／战争 | in_progress | 至少五合法候选比较，完整选定路径材料后置；已有五婚约候选、一次婚约、双向关系与冷恢复窄loop，但双方8岁、无联盟／成年履约；战争研究与实现已全面开放，按当前实际价值推进 |
| M6 谋略／制度／活动 | in_progress | 一scheme、一囚犯或制度动作、一非宗教决议或法律项目、一完整活动生命周期；CA1法律子项已闭合，其余不能省略 |
| M7 多身份长局 | in_progress | 多ruler／seed／government；checkpoint及自然继承后恢复同一高层intent。当前feudal44feature已读，ordinary目标hook静态ready，Robert实际恢复与第二seed未完成 |

新Council正式consumer（独立holder/task回执→next）、ordinary current-government adapter、M2条件stress policy都已分包完成必要窄fixture并提交。static-ready 不能替代尚未触发的实际业务。

宗教本轮有Rite/Faith/Religion、29 doctrine槽／94 source／49 selectable、tenet实际空槽合法null、AI observed_no_ai（controller_count0）的只读成果。Tenet materializable/final selectable都是0，不捏造选项；无真实controller时不推断AI timer。通用宗教动作／完整OODA仍未交付，复用既有原生树和专题，休假期间未新开研究。

### Robert准备包仍是 file-only

`B/m7-campaign-live-next/robert-12002-preparation/` 保存 `SOURCE-INVENTORY.json`、`FILE-STAGING-RECEIPT.json`、`operator-manifest.json`、`original-pair-sample`：旧Robert full4028／save anchor4025，goal合法null，三账本及原配对保留。没有执行官方1.20 profile/rebind／preflight／真实兼容恢复，不能宣称继续3153后的任何一天。

其中最初runtime指向6a91fa6，应在未来官方准备时采用明确的新冻结runtime与匹配源码，不能绕过9ce Feast修正。使用普通lifecycle，不手填goal、不截断history、不把当前rogue计入Robert。当前休假本轮没有启动此包。

## Git、CI与保留目录

原用户工作区 `Z:/ck3_mod_rewrite` HEAD d19e…，有大量历史未提交修改；未reset／stash／clean。源工作树 `Z:/ck3_mod_rewrite/.task-tmp/g2src` 收口前HEAD `df51c7a99ce74d258757f41edcfd3aa7d05ff781`；交付工作树 `g2dlv` 已普通push到公开master **`98506fa6e5a37790c8702c04d054c0e6d7cad57e`**。本交接及旧命令示例修复作为随后单独commit+普通push，最终映射记入 `B/delivery-state.json` 与 `B/r11-vacation-closeout/FINAL-DELIVERY-RECEIPT.json`；正文不预填未来commit。

本轮已交付：原生Sway专属意见口、Council正式消费、current-government目标、nonwar生产服务与必要测试、Feast实际hello兼容、M2条件stress、G2索引修正及Tributary版本断言。提交 `ed26e4a`（版本）、`ae56e608`（stress）、`220e2664`（索引）、`df51c7a9`（Sway实测）为源历史，公开重放hash按交付映射查询。

### CI真实状态

- 历史R9代码run36873544705／docs36878555646为SUCCESS，只代表对应旧HEAD。
- R11早期5e58acf／d47d700官方Step21因runner仍strict要求1.19.0.6而RED。最小两行修复引用现有CURRENT_GAME_VERSION，唯一实际失败方法用真实1.20CI输入PASS0.440s；没有改回产品descriptor或覆写上游configured executable选择器。
- 公开98506fa的[run36892558776](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/36892558776) 于2026-10-02 00:35:17 CST终态 **FAILURE**。Step21／27／32 SUCCESS，Step36仅 `event12002-natural-m2-execution.md` 两段旧shell fence共3违规；validator自身5tests PASS。
- 这个doc属于已经在途交付包，休假收口仅把两段示例改为Python结构化 `subprocess.run(argv)`，参数语义未改。受影响文档与本次交接报告的既有validator结果在 `B/r11-vacation-closeout/doc-validation.json`。最终push的云端CI在该push后单独查询留回执；不得把985的RED写成GREEN，也不借最终docs更新重跑整个旧矩阵。

985官方receipt：`B/ci-361-current-fix/official-ci-r11-final/98506fa6e5a37790c8702c04d054c0e6d7cad57e/final-receipt.json`，SHA-256 `a4489de52792187ece7b33aab65852801fcc25a546f25b2e59afba7149de7f73`。同目录的vacation-handoff-report保留逐step字段。

### 不要清理这些“临时目录”

`g2src/g2dlv/g2live11fix`、R11完整state与B是当前源／交付／冻结runtime／实机证据；没有在休假收口继续做Z盘清理。`B/r11-vacation-closeout/retained-source-status.txt` 记录源树剩余脏文件：历史WAR-CASH/PREWAR、旧Sway history/invalidation/threshold草案、pre-existing realm-law文档等均保留，未混入本次commit、未据未验证草案扩展R11资格。不要整树git add或把未提交文件当垃圾删除。原工作区历史修改也不等于本次交接已提交内容。

## 接手优先顺序（本轮均未执行）

1. 阅读最终配对／交付回执；保持full165和原账本，选明确冻结源码与匹配native候选。通过已有官方prepare/rebind与最新pins进入下一次paused新PID。
2. 先独立读取当前campaign root／关键材料，针对formal-r11-02第11调用实际RED做最小定位。已生效的CA1／perk／婚约零重发；技能cold与CA1cold分开记录。
3. 恢复适合当前状态的正式回合与正常时间策略，按已开放的战争研究和执行路径接续；Sway fresh progress／终态／独立modifier与下一回合消费，同时处理真实自然M2事件。无自然事件不能制造fixture来增加M2信用。
4. fresh Feast planner资格、预算、费用，合法时一次Start并观察完整结束；同窗口推进有实际价值的和平建设／Council机会／封臣干预。继续尊重原生合法与既有当前策略，不为凑计数降级内阁。
5. 当前seed的窄链稳定后才接旧Robert官方1.20ordinary兼容恢复及多seed／government长期intent与自然继承矩阵。宗教与战争均按真实决策依赖施工，战争研究、实现及实机已开放。

这些是依赖顺序，没有承诺自然Sway、成年婚姻或百年矩阵的墙钟日期。跨当前查询故障、自然触发、预算资格与旧save兼容后才可估工期；不能把余进度单位直接换算为固定天数。

## 报告与操作入口

原交接[2026-09-30非战争维护者交接](2026-09-30-nonwar-maintainer-vacation-handoff.md)提供历史领域入口；本文件覆盖当前授权、最新配对和R11事实。专题索引：[原生AI](../ck3-native-ai/README.md)、[正式nonwar服务](../ck3-native-ai/ck3-1.20.0.2-nonwar-service-mode.md)、[自然事件适配](../ck3-native-ai/event12002-natural-m2-execution.md)、[迁移进度](../ck3-1.20.0.2-migration-progress-2026-10-01.md)、[静态包账本](../autonomous-agent-progress/g2-offline-implementation-2026-10-01.md)。

实际R11成果／RED和休假调整写入[Oct2日报](../autonomous-agent-progress/daily/2026-10-02.md)与[W40周报](../autonomous-agent-progress/weekly/2026-W40.md)；Oct1已于00:02:06收口并立即召开Oct2早会。Oct2日报与W40仍是滚动报告，未冒充午夜／周末正式收口。日／周报告不需要新视频，本次未制作月报视频。

外部执行入口：`B/root-nonwar-live-next`（formal helper和原失败）、`B/m2-natural-live-next`、`B/m4-council-live-next`、`B/m4-intervention-live-next`、`B/m6-law-live-next`、`B/m6-sway-live-next`、`B/m6-feast-live-next`、`B/m7-campaign-live-next`。它们复用同一owner的现有driver/service，不允许并发抢pipe。官方启动流程参数以最新profile/phase JSON为准，文档旧h139命令不能直接当最新可执行命令。
