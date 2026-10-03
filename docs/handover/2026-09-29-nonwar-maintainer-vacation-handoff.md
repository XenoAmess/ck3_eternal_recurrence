# 2026-09-29 非战争维护者休假交接

**2026-10-03 战争授权更新。** 项目所有者明确命令“取消任何的非战约束”，并要求研究战斗。原战争研究停止、nonwar-only、战争执行暂缓、战争只能交由其他维护者等现行限制全部撤销；战斗、军队、行军、围城、战争理由、宣战、防御战争、议和及相关原生 AI、只读 bridge/MCP、策略、实现和实机验收均可继续。不得仅因涉及战争再次要求授权。本文历史冻结配置的 OFF、旧尝试 RED、当时未提交动作与未实现能力保留原事实，不能继承为当前禁战规则，也不能把开放授权写成能力已经完成。继续保持罗贝尔 actor29829、episode `native-29829-2bc2d599f7f9` 的原 ordinary campaign 与自然继承线，原生 AI 研究优先、exact-build 绑定、ROOT 唯一实机/pipe/Git owner，以及最小化、无焦点、无桌面输入。当前续接身份和保存锚点以[最新接续记录](2026-10-03-g2-v33-resume.md)为准，本文较早 episode、PID 和存档仅供历史证据。

> 本文按 2026-09-29 晚间（Asia/Shanghai）的已核证据写成。项目所有者要求温和收口在途工作并停止新工作；以下“下一步”供接手者使用，不表示本执行者已经启动。先看 [G2 主进度页](../autonomous-agent-progress/g2-requirements-and-execution.md)、[09-29 日报](../autonomous-agent-progress/daily/2026-09-29.md)、[W40 周报](../autonomous-agent-progress/weekly/2026-W40.md) 及 `docs/project-state/current-state.json`；实时 PID、owner、RED 必须查该状态投影指向的 live source，不能由本文代替。

## 停机与能力边界

- 本机最后一场 CK3 是 **R0373**：H3928 原始合法配对、PID 43736，完成普通宴会宾客**邀请前**正候选只读查询；运行结束后 CK3/injector/operator 进程树已回收。本交接收口时没有启动 R0374，CK3 未运行，也未占用桌面。战争同事在另一台机器；不要把他机器的实例状态推断成本机状态。
- G2 仍为 **3/8**：M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started。Robert 正式持久高水位仍为 **H3911/raw53219928、3,150/36,524 游戏日**；百年门 0/1、首整局 0/1、独立种子 0/2。R0369/R0370/R0372 的 h90 派生建设日期不能累计进 Robert。
- 本次增量里，R0372 在新 PID 实机证明建设冷恢复不再重置到期检查时钟：同槽 `hill_farms_01` 在原定 raw53156688 被再次查询，仍为施工中、剩余工作 raw95944458、月收入 raw87000。**未完工，也没有实际收益读回**。正式报告 SHA-256 `6B1CBAB1CD7108CB72794ED7F828A7C635F1521CA44D7139B81FFA2096AC51D4`。
- R0373 在同一暂停帧读到宴会邀请前候选角色 38293，`planner_join_raw=9300000`、旅行 0 天、到达 raw53219928 不晚于计划开始 raw53221344；四项成本为 Gold 100、其余 0。Stage5 `final_can_start=false`，军职限制仅有本地化显示文字，没有同帧独立角色军职读回。没有规则成员资格、最终邀请合法性、邀请动作、接受或 Start。正式报告 SHA-256 `809FBAE514E2E9AC099B21A0A2110ECA7A08A9AF96F6D8D84C3AE040261FA51C`。
- NW-LIFE：#657 修复 opt-in 战时私有查询失败或帧变化后同游戏日漏重试、开局 perk 预览提前占用机会；正式调用路径测试和精确 master CI 通过，**没有本轮生活方式点数或新 perk 的实机消费证据**。提交失败路径经源码追踪会停止当前轮、冷恢复重新评估或先核 pending receipt，未找到另一个可复现漏消费。
- NW-FAMILY：H3928 的 Emma 37265→Gerard 37267 提案仍为 pending，首继承人 38822 与 38718 已订婚；不能重复提案。新同帧伴随只读源码已合入（见下表），**没有实机读回或新增婚配**。
- NW-JOINT 继续复用既有选择器和 h90 派生的建设/婚配动作证据；联盟长期义务、战时建设现金承诺等缺项不能当零，也不能把候选数量当作能力提升。NW-COUNCIL/Faction/0110.c 只待合法自然场景，不为等待而另启 CK3。

## 已合入代码、候选和当前 Git

| 包 | 交付与界限 |
| --- | --- |
| #657 NW-LIFE | master `7eea9de9fc3158223f80bf92cdbae79bf0174434`，官方 CI 36568112631 SUCCESS；分支/worktree 已清理。 |
| #658 + #660 NW-ACTIVITY | 原生默认关闭规则读写入口与 Python 默认关闭的**规则只读**消费者，分别合入 master `4bcdea58812f0421001120d9214be7c6929b0825`、`91b999a7d4c46a3857bc982eaee887275dfb3f91`，精确官方 CI 36568408564、36569322046 SUCCESS；两个包临时分支/worktree 已清理。Python 正式 runner 把类别动作固定 OFF，缺规则成员与价值时 `hold`。 |
| #659 R0373 文档 | 09-29 日报、W40 周报和 G2 主进度页已记入邀请前阳性及边界，master `2b668a46b031c49e96f7c9fa533b915bd193a18f`，CI 36569132911 SUCCESS，临时分支/worktree 已清理。 |
| #663 NW-FAMILY | H3928 child pending 后同一暂停帧附读首继承人关系的私有入口，已 rebase-only 合入 master `4b924ae4eb1a3c45e7c5896ee0696b41be87d38f`，精确官方 CI 36570336033 SUCCESS；旧 #661/#663 清理状态见文末收口更新。无 live/no-launch。 |
| #662 NW-ECON | 战时建设只读机会 runner，建设动作 OFF，已 rebase-only 合入 master `f9e1f05a6a891467c60a02e2b2cc776438544042`，精确官方 CI 36570371013 SUCCESS；6 文件交付核验后临时分支/worktree 已清理。原始 H3928 配对的冻结候选 no-launch ready，**尚无战时建设实机读数**。 |

**已冻结、未执行的本机实机候选：** `Z:\m6-activity-h3928-guest-rule-state-candidate-20260929\CANDIDATE-INDEX.json`，SHA-256 `87FF7295C8DABEC6888AD5FD391457DC80EDA1183FACDC8F6DF1FB3484E783D5`；exact source `91b999a7`、官方 CI 成功、H3928 官方配对/no-launch ready。DLL SHA-256 `CCD8A506EC9605C45A722605D6969DA3FF5744259B387CB9F7CB71C848A674C5`，injector SHA-256 `85505C75DD7DA886D3C02AB69F57DE2C7E791014FB2707ED47007D72BA125A03`。只查 `activity_invite_rule_vassals` 当前 active/窗口绑定，规则动作、邀请、Start、游戏日期推进均 OFF。执行入口以索引的 `live_command.script` 为准，该脚本 SHA-256 `A09B57323FDB2761176B266387E83AA488E20E0B80F8DD82312F40A7915BD7B0`；输出目录尚不存在。**本执行者因休假指令没有运行该脚本。** 接手者启动前仍须重新核本机唯一实例、owner、匹配冻结输入和窗口状态；加载后立即最小化。若返回 `window_unbound` 或其他 unavailable，要保留 RED，不把它解释为规则未启用或无候选。

NW-ECON 另有 `Z:\nw-econ-h3928-wartime-readonly-candidate-20260929\CANDIDATE-INDEX.json`，SHA-256 `A8C2CB4DE6CD386F504AFC274EA50A9194745E5A4126E4BCF9D769711AF53C3C`；合格的是 `state-b`，官方 no-launch 报告 SHA-256 `729A8256FA32B34E04C787EB28304B6D15EFA61F9107DCAC4D02E50214020B69`，Release DLL SHA-256 `75862D0CA3ACBB44642DE0502721B414C646E316D3284E77CAF06524FE2F47F9`。运行参数模板在索引中，轮次须由当前 owner 用持久分配器分配。失败的 `state-a` 因原 driver 固定 pipe 不符而被拒，清理又被工具策略拒绝，保留日志，不可作为候选。

家庭 #663 只有源码和已停止的预构建；`Z:\family-h3928-companion-v1-20260929` 中的准备脚本 SHA-256 `1DE12870EC2A812D4F769FC2B65B9E3826C681630596B2304CB4CC6A70A14C67`，但尚无正式 state/manifest/no-launch，不能启动。该目录的 detached source 和部分 build/temp 是未运行准备资产。

## 仍在途的安全交接边界

- 宾客**逐规则来源**：现有 planner `+0x1590` 把同优先级规则合并，不能反推候选 38293 属于哪个 authored rule。[草稿 PR #665](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/665) head `24769baa0ba512138691985f4e6bf5ac35c6203a`，分支 `nw_activity_guest_rule_provenance_20260929`、工作树 `Z:\gtrp_20260929`；Debug DLL 编译与两项聚焦 CTest 2/2 通过，官方 PR CI 在本文收口时仍运行。它只在自然刷新时被动记录已 active 规则的临时成员，不额外执行 scripted effect。规则 inactive 或无自然刷新保持 typed unknown；**未实机、未合入**，分支/worktree 保留，不为填字段擅自激活。
- 宾客对主办者好感：草稿 PR [#664](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/664)，head `1f16756aaeea3707f4be3e09a655bb015faa3362`，分支 `NW-FEAST-GUEST-VALUE-R0373`，工作树 `Z:\m6-feast-guest-value-read-20260929`。复用原版 `ReadGiftOpinionExact11906V1` 的独立模块/transport 与聚焦测试已推送，PR 官方静态检查成功，但 **bridge.cpp/CMake/mailbox 尚未接通**；未合入、未实机、分支/worktree 必须保留。源码文档明示缺口，不把草稿视为 MCP 可用。
- 固定战争交互目录是 `C:\Users\xenoa\OneDrive\WAR`，战争同事在另一台机器。最新本机已读回复 `NW-ACTIVITY-R0368-ARMY-ROLE-DEPENDENCY-20260929/RECEIVER-RESPONSE-NW-R0368-ROLE-QUERY-REVIEWED-SOURCE-v6.json`：其 4996e2763 是已复审**源码**，原生构建/fixture、DLL 和 live 军职行仍 pending；R0368 原帧 commander/knight、safe release 仍 unknown，不能据本地化提示自行清军职或宣称宴会可 Start，也不能把 Robert 战争 RED 当作解除。战争公式、路线与军事能力可由当前执行者按原生研究优先规则继续研究和实现；原战争维护者的已交付证据与接口直接复用，不再以人员分工阻止推进。
- PRV008 原冻结 GO 只覆盖 actor31853、episode native-31853-af642d76cb41 的普通封建有界路径；ZIP SHA-256 `B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3`。本次未改动 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR`、release 或 qualification；跨机器真实获取性本次未验证。新 Robert/非战争候选不能借 PRV008 资格。
- 根工作区 `Z:\ck3_mod_rewrite` 是历史脏现场，且本机该目录若干近期 tracked docs 文件缺失；本次写文档只在独立 Z 盘源码 worktree，不能在根目录 reset/clean。受管 temp/cache/build 均在非 C 盘。旧 #624/#622 等因工具策略拒绝而残留的工作树不得绕过拒绝强清。

## 接手顺序

1. 先查本文收口更新、`git fetch origin master` 后核 exact SHA/PR/官方 CI，再查状态投影 live source 与本机 CK3/injector/operator 实际 PID。只消费已匹配的制品；无 PID 不等于别的机器或账号可启动。
2. 优先用上面的冻结 H3928 宾客规则**只读**候选在唯一窗口做一次有界实机；正常加载后最小化。独立核同帧规则 active、窗口绑定、Stage2 receipt、save/date/gold 不变及进程回收。若 `window_unbound`，先定位原版绑定路径；不要凭 group count 猜成员。
3. 之后处理已合入但未实机的 H3928 家庭伴随读、战时建设只读候选。家庭必须重新官方配对/no-launch；经济只用 `state-b`，仍须确认战争现金占用，不能只因可负担就开工。生活方式只在新角色/新日期有真实点数时做配对正例；不重复 H3928 同日 0 点读数。
4. 保留原 h90 派生建设检查钟和有效 checkpoint，继续到完工/效果独立读回；不拿开工 receipt 或预测 +0.35/月冒充收益。该历史 Robert 战争日期门的能力缺口按真实生产入口补齐并实测；当前执行者可继续军职与战争能力施工，并按同帧合同消费，不再把等待指定维护者作为授权前置。
5. 每个新动作仍需正式观察、合法性/价值、typed 提交、独立后置、下一 turn 与必要 cold restore。合入后核精确官方 master CI、blob 和临时分支/worktree 清理；进度页同步真实能力边界，G2 定义与计数不改。

## 收口更新

- #662 精确 master CI 36570371013 SUCCESS，原 tip `c5683c1` 核验后远端/本地分支与专题源码 worktree 已删除；合格 `state-b` 候选与策略拒绝清理的失败 `state-a` 日志均保留。没有 CK3 启动。
- #663 精确 master CI 36570336033 SUCCESS，原 #663 head `7171a4e` 与 master 7/7 受影响 blob 相同。旧 #661 tip `7282621` 与 #663 tip 删除前均重新核过；两远端分支、本地引用及 `Z:\fchildcompanion40` 源码 worktree 已清理。保留未运行的家庭候选准备资产，未做 no-launch 或 CK3。
- #664/#665 都是未合入的草稿 PR，前者还缺原生分发接线，后者缺实机；#664 PR 官方静态检查成功，#665 一项官方静态检查截至本文写入时仍运行。两者均不清理分支/worktree。
