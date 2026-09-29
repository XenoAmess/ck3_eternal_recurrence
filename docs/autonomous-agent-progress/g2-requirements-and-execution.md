# G2 全游戏自治需求与执行记录

本页状态摘要更新于 **2026-09-29（Asia/Shanghai）**。8 项里程碑的定义、分母、状态和通过条件以
[`g2-requirements-v1.json`](g2-requirements-v1.json) 为准；工作包投影见
[`current-state.json`](../project-state/current-state.json)，当前 PID、owner、RED 须按其中声明的
**Operator live source `operator_get_status`** 实时核查，不能以 Git 缓存投影或本页历史段落代替。
已收口的 09-28 增量见[09-28 日报](daily/2026-09-28.md)；新提交见[09-29 滚动日报](daily/2026-09-29.md)及[W40 滚动周报](weekly/2026-W40.md)。`current-state` 的持久高水位仍以 R0321 的 H3911 checkpoint 为据；R0328 h3915 与 R0329 h3922 均为同日期后续候选，不能增加游戏日。
Robert 最新已投影来源为 **h3911/raw53219928、3,150 日**；`current-state.json` 仍记录 R0321 战争 RED。R0328 Emma 母系提案在私有 opt-in 候选中 typed 提交且 ledger `receipt_pending`；#515 提供 H3915 sidecar 配对后，R0329 新 PID 已原生读回 `pending/outbound active`、无重复提交，但**没有婚姻物质结果**，wrapper 分类仍 RED。`g2-requirements-v1.json` 的 `current_work_package` 为 **NW-2026-09-26**；实际 PID、owner 和 RED 仍须查询上述 Operator live source。
玩法覆盖与 Native/MCP 研究依据见
[`g2-ck3-gameplay-coverage-gap-research-2026-09-12.md`](g2-ck3-gameplay-coverage-gap-research-2026-09-12.md)。

R0329 原始 wrapper 将第三步安全截停误计为重复提交风险；基于原始报告的独立纠正回执 SHA-256 为 220428EF332EE187D58D704102F4EFB9674D2CECB4D7C4B6454C26D678173997，确认内层正式冷读合格、提案仍 pending 且没有物质婚姻结果。原始 RED 报告保留。战争维护者在固定 OneDrive WAR 目录返回 H3911 attempt3：no-launch 预检通过，但实机首次 native snapshot 超时，未完成同帧战争查询，也未交付可消费的战争现金、预测或安全路线；因此 Robert 日期和 Emma pending 年龄不增加。来源见[09-29 滚动日报](daily/2026-09-29.md)。
#517 已把 R0329 类型的在途子女提案后续结果读回接入正式消费：同一 PID 首次 cold 读后，较新 native revision 可走 ordinary 结果；战争 gameplay 步骤会在只读结果之后下一 turn 重新选择。#518 已保留战争 planner 无 selected_step 时既有建筑的到期回执/收入只读查询，原战争 RED 单独保留。两项分别进入 master 738dc2f 与 67a5219，精确官方 CI 成功，临时源码分支及工作树已清理。它们是源码/测试修复；尚无新的 Emma 接受/拒绝或 h90 完工/实收实机证明，G2 仍为 3/8。

09-29 02:00 增量：H3922 连续提交与冷读两份证明的官方配对源码已到 master `5e8806f4d66867ab545e0421d6593d5b07fcd6df`，isolated prepare/rebind/no-launch `ready`（报告 SHA-256 `E9390C166A7C557545EC4ECC362F72A3F74057A8B2F4BBA68DA9DA2BB4ECC921`）；**尚无新 revision 的 CK3 运行或 Emma 婚姻结果**。该提交由集成负责人隔离 rebase 后直接线性推 master，exact CI #36461010717 SUCCESS、临时源码已清；原 PR #523 在 GitHub 为 CLOSED/无 mergeCommit，推送时 expected CLA gate 被 bypass，不写作受保护 PR 合入。#520 法律私有 active/candidate key 读口与 #519 feast ABI 缺口文档分别经 GitHub rebase merge 至 master `e23f32b`、`eda8487`，exact CI #36461409774、#36461444189 均 SUCCESS；尚无对应 H3911 live 资格/成本或活动查询。#521 sway 私有 paused query 源码经 GitHub rebase merge 至 master `dfd7995`，提交前 exact CI #36461679206 **SUCCESS**，负责人已回报远端/本地临时分支与源码 worktree 清理；无 sway live 读回或动作。**没有新增 CK3 动作、持久日期或 G2 里程碑**；Robert 仍 H3911/raw53219928、**3,150/36,524 日**，G2 **3/8**，Sway 仅为默认关闭的私有读口。

09-29 02:18 实机增量：R0330 从 H3911 正式配对启动唯一最小化 CK3 PID34848，暂停/map-ready、actor29829、native revision3；私有 Sway 查询首 turn 在原生 root 返回 **`native_scheme_observation_red:root_unavailable`**，正式报告 SHA-256 `0F33C7A094BB3F88A83518ED9759EC528C69364BBBBDED65D118D2FB20C00630`，源 save 未改变且进程树已回收。尚无 Sway 合法性读数、typed 动作或日期，RED 根因待查；不能据此判断目标不合法。Emma pending 仍待新 revision；Robert **H3911/raw53219928、3,150/36,524 日**和 G2 **3/8**不变，详见[09-29 日报](daily/2026-09-29.md)。

09-29 02:47 增量：#528 Sway root 修复与 #529 law 私有 paused 读口已分别经 GitHub rebase 合入 master `7bf30f0`、`38085f9`，exact master CI #36465243293、#36465744499 均 SUCCESS，临时引用已清。H3922 同日私有实机 R0331 首 turn 报 `native_scheme_observation_red:container_unavailable`（正式报告 SHA-256 `97AE6824B54D4A4FF1D6828D920735F047701DE66AAC67D398C443D470B05AE7`），R0332 首 turn 报 `native_law_collection_red`（报告 SHA-256 `FC84DBDDFEFD1FB0AB4228E6DF8F2705DBA39194CE0FF9FAE5F86421DD6D7090`）；两轮均无有效查询、typed 动作、日期，来源 save 未变且树回收。尚无 Sway 原生合法性或法律 CanEnact/成本，不能据此判无机会。旧 H3911 faction `run.cmd` 因 R0327 已消费且现配对不符，不列 READY；R0327 仅当前窄政策 `no_eligible_direct_vassal`、0 礼金动作。Robert 仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**；详见[09-29 日报](daily/2026-09-29.md)。

09-29 03:04 补记：WAR 接收端 H3911 attempt4 四项同帧**只读**回执 SHA-256 `B36C84B3A40633A1C22A44B27E9F1D7301265876EB18A7759A565B99BDE647FE` 明确两支 defender；到2629预览首跳 168 raw hours，而接触窗只证明前24 raw hours 无接触。未授权 move/attack/date，战争现金未知，R0321 forecast RED 未解除。#530 活动研究文档和 #531 报告包 exact master CI #36468100584、#36468391822 均 SUCCESS；#532 Sway 原生空容器/generation-zero 适配与 #533 私有 opinion 价值输入已合入 master `c1349caa`、`8965a920`，exact CI #36468756683、#36468848363 均 SUCCESS、无后续 live 结果。**没有新增自动动作或 Robert 日期**，仍 H3911/raw53219928、**3,150/36,524 日**，G2 **3/8**；详见[09-29 滚动日报](daily/2026-09-29.md)。

09-29 03:19 实机增量：R0333 H3922 私有 Sway 容器已可读，但首 turn 原生预条件 `native_sway_precondition_red:native_precondition_red`，正式报告 SHA-256 `A45EBD2DA4262FE2468D7FE932744C7BF0C3D913D77FB7962FDC9C2AF37E3F51`，仍无 Can Send/价值/动作。#534 law 候选集合源码经 GitHub rebase 合入 master `9659eb69`，exact CI #36469283389 SUCCESS、临时源码已清；R0334 H3922 私有 paused law **只读 GREEN**：active crown0，crown1 final CanEnact=true、prestige 费用 207，crown2/3 blocked；active confederate partition、其它三种继承法 blocked。正式报告 SHA-256 `522BCD5AE66297AA2C518C2CC006247977D1D7DF32F150D057B64B8D2C7B973B`。当前 prestige 足够，但 CA0→CA1 封臣好感/20 年冷却代价与战时机会成本未估净值，法律动作仍 OFF；**原生合法不等于 submit-ready**。两轮均无 typed 动作、扣费或日期，来源 save 未变、进程树回收。Robert 仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**；详见[09-29 滚动日报](daily/2026-09-29.md)。

09-29 03:23 源码增量：#535 活动 planner 默认关闭的私有 paused 诊断已合入 master `29df397cd05996c9b21fb9d1bdc64b72f39259a6`，exact CI #36471580131 于 03:26 复核 SUCCESS；**没有活动 CK3 live**，费用、最终 CanStart 和活动动作仍未知。此局部源码不改 G2 **3/8** 或 Robert **3,150/36,524 日**。

09-29 03:39 增量：#536 私有 Sway 预条件阶段诊断已合入 master `03f688e94d9a1dd14591d3b2ae79a3850721668b`，exact CI #36472017769 SUCCESS、topic 清理。R0335 H3922 最小化实机首帧返回 **`native_sway_precondition_red:native_precondition_red:context_options`**（报告 SHA-256 `4D07E95205547080D3F705878B64389783AFA1622FAE3E956A8A0C099B822056`），没有完整 Sway 查询、typed 动作或日期；来源 save 未变、树回收。#539 尚在源码 PR 检查，未实机验收，不能宣称修复或目标不合法。Robert 仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**；详见[09-29 滚动日报](daily/2026-09-29.md)。

09-29 03:57 实机增量：#539 原生空 context option 处理已合入 master `c72bd4ba808e04fe344422361eab26066f466802`、exact CI #36474116242 SUCCESS；R0336 H3922 私有 Sway paused read-only 首次 **GREEN**，target32716 对玩家 opinion -5、active scheme0、native complete CanSend=true/`legal_now=true`，报告 SHA-256 `7A42B388A8EE612A16DF4BC326C6F4AFC2FB924C297920CC082AC8F20B18E316`。这是合法机会的观测，**没有正式价值选择、typed 动作、下一 turn或恢复**；来源 save 不变，Robert 仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**。详见[09-29 日报](daily/2026-09-29.md)。

09-29 04:40 增量：#541/#542 私有 typed Sway/正式消费者源码已合入 master `84a485d`、`15dc98f`，exact CI #36478019259/#36478770812 均 SUCCESS；远端临时分支已删，本地源码 worktree 因自动清理策略拒绝保留。R0337 H3922 首 formal turn 在 **submit 前**由 Python `played_character` 形状不匹配触发 `ValueError` RED（正式报告 SHA-256 `631A5F647B46CC0F713D7A76A226E12622015CA9867555A637BB712D252DDB09`）；同帧原生 opinion -5、active0、CanSend/legal 仍真，但没有 typed 提交、receipt、checkpoint 或日期。WAR H3911 现金政策回复 SHA-256 `ACED0B0D4BCA99FA06D2CE175BCB9B2C7C4DA5C72392D303C77B789C8D7C41E3` 和接收 ACK SHA-256 `4DEFB13FBFFFA7DF16786376472FE7F57D543D47B3356494D0FE56F2638B01C8` 仅确认储备/期限/风险/未来上界仍 deferred/null，非现金能力或花费授权。Robert 仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**。

09-29 06:25 增量：#543 compact/full frame 修复已合入 master `a468ff3e422536eed5afa9975a34da556265e55b`，exact CI #36481788598 SUCCESS。R0338 H3922 正式消费者越过 Python 入参门，但 native executor 回 `private sway native RED: sway formal executor unavailable`，`submission_unresolved/not_qualified` 台账不证明动作接受；正式报告 SHA-256 `8858186F7CE286F076E1183EC6D50384F93522D9DACD0D76CF74F907E83F48B1`，源 save 不变、树回收、0 动作生效/0 日期。白名单修复尚待独立实机；Robert **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**。
09-29 07:04 增量：#545 原生 Sway executor 接线已合入 master `e7f7e5ab5751d4cca2f5bae9842e650f516a89e8`，exact CI #36493861196 SUCCESS。R0339 H3922 typed submit **一次**，得到 `submitted_verification_pending` ACK，但 receipt `native_sway_receipt_red:glue_red`、台账 `receipt_pending`，正式报告 SHA-256 `A0453509B1A8EACCB16DEB090FC1623CDCC7B5F055B8CFABFD6D760ABF1E79FD`；同日 H3924 checkpoint 的独立二进制比较 SHA-256 `1E07D6294BE02DDAF0917945F4E7F6580EE096FC97C7B4285DCF39DE47067B92` 发现新增 actor29829→target32716 Sway 形态行，**不代原生完整后置**。R0340 新 PID 冷读在 `native_scheme_observation_red:core_rejected` 失败（报告 SHA-256 `14F8D0EBD839A1B03C6E6DC96091E0EFAD3A403774232B7CCE43DF3188E4D2E7`），0 成功查询/动作/日期；C++ core 与 Python pending 修复在途。没有 Sway receipt、下一 turn 或冷恢复闭环；Robert 投影仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**。详见[09-29 日报](daily/2026-09-29.md)。

09-29 08:08 增量：#549 Python 官方 prepare-state 子女 pending 跨 Sway checkpoint 配对续接已合入 master `566c84fb4c4a43bdc58372371f6363e0ebca8641`，exact CI #36498961975 SUCCESS；R0341 H3924 借 #546 原生 core 诊断读口将旧 `core_rejected` 精确为 `metric_invalid:row0_progress=0:row0_goal=355`（报告 SHA-256 `B8D07329860EF475A1B6719BBE0B7F3A756963B3B8F9BB20FB03BD796A341AAC`），0 成功查询/动作/日期。#550 goal 区间修复已合入 master `8695b2860ac07ab141abf39810a9c0c284d44160`，exact CI #36500543739 SUCCESS；R0342 **新 PID** 从 H3924 读回 active scheme 数1、matching Sway=true，并将 R0339 原 action_id 判 `applied/postcondition_verified=true`、无重复 submit（正式报告 SHA-256 `EC5BFA99018974AE09C0423D6F24431295194604F9D2B99EADFD9C7EA12EA1A0`）。H3928 同日 checkpoint/save、driver 和 resolved ledger 已保存；`native_receipt=null`、`next_turn_consumed=false`，下一 gameplay turn 与 resolved ledger 再冷恢复仍待验。Emma pending、战争现金、PRV008 边界未变；正式 Robert **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**、百年/整局/种子 **0/1、0/1、0/2**，M6/M7 不提升。详见[09-29 日报](daily/2026-09-29.md)。

09-29 08:44 增量：R0343 从 H3928 保存配对及 `resolved` Sway ledger 在**新 PID43540** 冷启动；私有 paused 只读原生查询在 raw53219928 同帧读到 actor29829→target32716 的 active scheme 数1、matching Sway=true，目标 opinion -5，当前重复发送的 native complete validator 拒绝。正式[报告](Z:/m6swayh3928resolved-cold-read-live-20260929/operator-runs/sway-h3928-resolved-cold-read-1/formal-report.txt) SHA-256 `E72435E04EF66795EDEFA31232D87CB7AACA022A1B3E161FB895BBD61C3960FE` 为 `read_only_observed/ok=true`，**0 formal turn、0 gameplay/日期**；这复核了既有 Sway 在另一新 PID 的游戏内 active 状态，并非 resolved ledger 已由下一策略 turn 消费。R0344 又从 R0343 结束的 H3928 save/driver 配对在**新 PID42836** 做 1-turn 正式候选，仅成功执行 `query-war-termination-options-16777231`（query1、gameplay0、无 checkpoint/日期），未走 Sway 下一 turn 消费；[报告](Z:/m6swayh3928nextturn-live-20260929/operator-runs/h3928-next-normal-turn-1/formal-report.txt) SHA-256 `53564EA6B63FA3A87A622AAFE200A9E043E5BAA072B3513F1FE1322CFA51A016` 为 `turn_limit/not_qualified`、operator exit1，进程树回收。两轮台账仍 `native_receipt=null`、`next_turn_consumed=false`，没有新 Sway typed 动作或正式日期；下一 gameplay turn 合同仍待验。G2 **3/8**、Robert **3,150/36,524 日**及长期门 **0/1、0/1、0/2** 不变，M6/M7 不提升。详见[09-29 日报](daily/2026-09-29.md)。

09-29 08:50 增量：R0345 以 R0343 后 H3928 save/driver 与相同 `16d6806` DLL 尝试 8-turn 普通正式入口，在新 PID104056 实际尝试6步、成功5步；计数 query4/gameplay1，其中唯一 `gameplay` 类是 `preview-move-army-83886367-to-2629`，证据 `no_semantic_delta`，**无已确认的物质游戏动作或日期推进**。第6步 `planner_blocked`：`qualified_forecast=producer_unavailable`，provisional `same_frame_encounter_scope_mismatch`，combat inputs v3 虽 `available`，但 `monte_carlo_ready=false/planner_usable=false`；[正式报告](Z:/m6swayh3928normal8-live-20260929/operator-runs/h3928-normal8-1/formal-report.txt) SHA-256 `5DDFB67E006E44A1C60258BD4C669EC737E55861BADEA271EF77AABE52C79C57` 为 `blocked/failed`、operator exit1、树回收。H3928 save 与 resolved Sway ledger SHA 未变，`next_turn_consumed=false`；战争模型缺口由维护者处理，Sway 下一正式 gameplay turn 仍未完成。G2 **3/8**、Robert **3,150/36,524 日**及长期门 **0/1、0/1、0/2** 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 09:49 增量：#554 feast planner 入口/阶段门原生静态追踪、#555 `task_collect_taxes` 候选替换价值静态探针、#556 feast typed event payload 原生追踪，分别经受保护 rebase 合入 master `586851425aefe8c5d2498d08b4eebb6294e18918`、`375ae5c73347b68a01ed24dede08be4f4f91cadf`、`2e7c3c3f551258b75bc18ee4cbdbb439b1f42af9`；对应 exact master CI #36506679002、#36507151940、#36508219434 均 SUCCESS，临时分支/源码工作树已由各负责人清理。活动仍缺玩家最终 location/configuration/cost/CanStart 及动作，议会税收完整原生候选值与机会成本未观测；没有 CK3 实机或新正式消费。

WAR/R0345 V3 receiver ACK SHA-256 `436F9C17CE4304D472AC52563FBB13CA51D199FBA16E40BE265E3F4D72B11D83` 证明指定 raw excerpt 的传输与哈希，接收端诊断 SHA-256 `5E1CA252034AFA483F3557F5F5B4ACCBFEE8A6D73AB4FE314994A5CA380E2439` 将 V3 输入限定为只读可得、**合格预测仍 RED**；完整 46 MB parent driver 未由接收端哈希，不能把摘录等同全部原件。接收端 bounded noncontact 回复 SHA-256 `97C7208DC081DA5D281E40876B591B4C1D9C5EFED7ECFD2DBADF1844FD446ECB` 明确 H3928 当前**不能**据 target2629 假设路线的一天 contact-free 查询推进一天：当前原生证据先缺 target2610 同帧驻留查询、已广告的 proof-bound composite 与完整受控军队/敌方范围；现金/战争风险属于另外评估的一天策略预算，不是纯 native 一天执行器的固有合法性条件。来源 final-frame 摘录 SHA-256 `A8EAC0C490F8513F1DC40C9C34077DE3C352BAE7C56B2DE047525D598E8ED7F8` 发现 target2610 查询仅有旧帧记录，raw53219928 最终系列为 0 条，完整最终 snapshot/capabilities、金钱与目标围城状态未在 driver 留存；接收 ACK SHA-256 `E52E1737CB531780D2C3BCCF02E0D6088966D2E09C0290A1FFCFED5138CB7CBC` 只确认小文件部分当前帧传输。v2 澄清 SHA-256 `EF235F4CCFA490F7F6812B49643B5F4A8F2F6EFA52C363B40FA615607A6CB988` 将 native proof 与策略现金假设分开；v3 收口 SHA-256 `CC86218B5F4C11876B65BC7FAAAB871B7EAF8D6F8DE7C93EADBC89EF29750D37` 确认离线 H3928 证据已用尽，只有新独立只读同帧查询才可能补当前证明，仍不授权推进。来源已提出待战争维护者评审的本机只读 target2610 runner 请求；接收端 offer ACK SHA-256 `9AB319A0C026CA0D6D1C767DE5BBECA5AF51898B37F87CEB9EA79FD2FF1F2D51` 仅为 `offer_received_decision_pending`，**尚无经评审 runner、CK3 新轮、动作或日期**。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、长期门 **0/1、0/1、0/2** 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 10:11 实机增量：#557 `activity_feast` 原生类型注册表与规划器队列追踪已合入 master `1674d81`，exact CI #36510008329 SUCCESS 且临时源码清理；#558 三份进度文档已线性合入 master `082aaf9`，exact CI #36510923780 SUCCESS 且临时源码清理。R0346 以 H3928 合法配对在新 PID132228 作**一帧只读**原生活动规划器诊断：同帧 `native:3`/raw53219928 读到 planner 存在、widget 已挂接但隐藏、阶段2、HostView 当前类型为 null；配置费用和最终 CanStart 仍 `unknown`。正式[报告](Z:/m6-activity-h3928-diag-20260929/operator-runs/h3928-diag-2/formal-report.txt) SHA-256 `3D440F9D2E9F79891D96C80A94096BA75A66BD53C8D80E82FDB53D5B382C3E73` 为 `read_only_observed/ok=true`，0 turn/游戏动作/日期、存档不变、进程树回收；不把隐藏阶段2或空费用认作活动机会。下一施工入口为原版 `activity_feast` 打开路径后的 widget/费用刷新和阶段5最终合法性读回。**没有新增活动自动动作**；G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、长期门 **0/1、0/1、0/2** 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0347–R0349 实机增量：R0347 的 H3928 子女婚配冷读候选虽通过官方配对/no-launch，但候选 DLL 的四项 M5 家庭私有 CMake 开关均为 OFF，首帧报 `player-child marriage query RED: unsupported native gameplay step`；[正式报告](Z:/m6-child-h3928-pending-read-20260929/operator-runs/child-h3928-read-1/formal-report.txt) SHA-256 `BCEE86EB1DF9D5241FB8D143C7438AEDCE3294E8F76196FB0363254F2F473693`，0 成功查询/动作/日期、树回收。R0348 在同日私有[读回](Z:/ck3_mod_rewrite_process_assets/nw-faction-h3928-rows-20260929/evidence/R0348/faction-readback.json) SHA-256 `76E4B0322BDE63C2E0ACC26470829CA35A8FAE5C155F35A2B18A47A604FF956B` 中观测到针对玩家29829的派系188，但已发布 targeting row 的 leader=null、member=[]，与10名直属有地封臣无可匹配对象；[verdict](Z:/ck3_mod_rewrite_process_assets/nw-faction-h3928-rows-20260929/evidence/R0348/verdict.json) SHA-256 `6504EB6FA1EF5C6CBA86CA97FE56370219B5CDB4E381C53DF3EA6DF0F7C5B040` 为只读、0 礼金/日期。R0349 用四项 M5 私有开关 ON 的新 DLL 和官方[配对索引](Z:/m6-child-h3928-pending-read-v2-20260929/CANDIDATE-INDEX.json) SHA-256 `6F66F5C1AA6F761BBBE51BFBBEC314E943B98DA13A1EBAF8EF75141B83D244E4` 在新 PID 冷读 Emma37265→Gerard37267：原提案仍 `pending`、outbound `active`、age0 天、AI reply cutoff7 天；[正式报告](Z:/m6-child-h3928-pending-read-v2-20260929/operator-runs/child-h3928-read-v2-1/formal-report.txt) SHA-256 `75166276154F69E1BB42863638CD7B305B08A499C472E8444DCF019B2DD3C149` 为 `read_only_observed/ok=true`、无婚姻/联盟物质结果、0 新提案/日期，树回收。三轮只补故障定位与当前状态读回，**没有新增正式非战争自动动作**；同日 H3928/R0349 与 R0348 的同日 h3933 均不增加 Robert 持久游戏日。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、长期门 **0/1、0/1、0/2** 和 PRV008 冻结边界不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0350 活动实机增量：H3928 的私有 `activity_feast` planner open 候选在同一 paused raw53219928 原生 dispatch 一次，widget 已挂接且 `visible=true`，新帧 `planning_stage=1`；旧后置硬要求阶段2，故 `open_status=postcondition_failed`、`accepted=false`。[正式报告](Z:/m6-activity-h3928-open-candidate-20260929/operator-runs/feast-open-1/formal-report.txt) SHA-256 `4978EC4C2EAC90C0D27E2E7F092D3579A3EAB89D181872220FFBCA40B9408CDB` 为 `stopped_on_error/failed`、0 成功 turn/游戏日期、源 save 不变、进程树回收。随后 exact 1.19.0.6 原生调用链查明：`special_option_category` 会在类型选择后把合法类别选择 UI 导向阶段1；**阶段1本身不是失败证据**。R0350 未单独发布所选 feast 指针，因此该 RED 仍保留，不能反向确认为成功打开；配置费用、最终 CanStart 与宴会动作均未观测，修正后的源码尚待独立实机。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 冻结边界不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0351 实机增量：在独立 h90 派生候选中，正式 M5 同帧选择器先从 6 个合格候选选择 `building:2174:628:1`，提交 `hill_farms_01`；同槽原生回读金钱 raw `34,490,601→24,490,601`（扣 100 金）、施工中、剩余工作 raw `109,500,000`。随后从 5 个合格婚配候选按家庭政策优先序选择继承人 38822 与 38710，正式提交一次，先读到 pending；时间从 raw `53153760→53153976`，报告明确 `elapsed_days=9`，随后独立读到**实际订婚**和玩家 29829 与接收方 32266 **双向联盟 allied**。[正式报告](Z:/ck3_mod_rewrite_process_assets/m5-family-h90-sort571-candidate-20260929/run-formal-12/formal-report.txt) SHA-256 `C9BAD73D1756E0180F93C4A2A0AC1616363BEBB502666A22740FD058F03FFE23` 为 `12/12 qualified/ok=true`、进程树回收；[候选索引](Z:/ck3_mod_rewrite_process_assets/m5-family-h90-sort571-candidate-20260929/CANDIDATE-FREEZE.json) SHA-256 `1312AF3BA115D0AA420418E128BCC6262ACE906C54F027AFCFBEEFD1B0430091`。这是派生场景中的正式建设与婚配选择、扣款、开工、订婚及联盟物质结果；施工**尚未完工**，收入增量仍未知，且 R0351 **尚无新 PID 冷恢复**。这 9 个派生游戏日不计入 Robert。

09-29 R0352 实机增量：H3928/raw53219928 官方配对与默认关闭的家庭 pending-result 候选在新 PID56288 仅执行一次 `query-player-child-matrilineal-marriage-result-v1-private`；Emma37265→Gerard37267 原提案仍 `pending/outbound active`、age0/cutoff7、`material_result=false`，未重发提案，同日 h3933 checkpoint 和 pending ledger 保留。[正式报告](Z:/nw-family-h3928-pending-recovery-20260929/operator-runs/pending-recovery-1/formal-report.txt) SHA-256 `F4AB308E7FDB90DC97F3207F92212D7487BFE74AAB74A44EB6B795C768B35296`：内层 1/1 查询执行成功，但通用 bounded 资格要求 `visible_gameplay/date_advanced`，本次纯 paused 结果读取均为 false，整轮 `turn_limit/not_qualified/ok=false`，operator exit1；进程树回收。该**资格 RED 保留**，不能把一次成功查询说成整轮 GREEN，也不能把 pending 说成婚姻结果。修复范围是结果专用且默认关闭的 bounded 验收合同；Robert 持久 **H3911/raw53219928、3,150/36,524 日**、G2 **3/8**、百年/整局/种子 **0/1、0/1、0/2** 及 PRV008 冻结资格不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0353 活动实机增量：修正阶段1后置与所选 feast 验证后的 H3928/raw53219928 私有候选，在新 PID57224 的同一 paused `native:3` 通过一次 `open-activity-feast-planner-v1-private` 原生 dispatch；receipt 为 `open_status=opened`、`selected_feast_verified=true`、widget `attached/visible=true`、`planning_stage=1`，`same_frame=true`。独立[正式报告](Z:/m6-activity-h3928-stage1-candidate-20260929/operator-runs/feast-stage1-open-1/formal-report.txt) SHA-256 `345727EFB71839482EE77A16A1319871D5423049A8391D1490B2660F284ADBED` 为 `private_activity_feast_planner_open_observed/gui_open_observed/ok=true`、进程树回收；[候选索引](Z:/m6-activity-h3928-stage1-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `5F23006D4127B9D275A10F4948B36DAD769C9305412E8662A8EE70DEFDABCCCB`。这只闭合**私有 planner 打开/阶段1 可见后置**；所选活动类别选项、配置费用和最终 CanStart 仍未读出，宴会未开始、未扣费、无收益或日期。R0350 原 RED 作为旧候选结果保留；G2 **3/8**、Robert **3,150/36,524 日**和 PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0354 冷恢复增量：R0351 派生 h90 最终合法配对 h107/raw53153976 从新 PID150508 继续，正式第1–3 turn 分别读回**同一建筑槽**已施工、剩余工作 raw `108,500,001`，继承人38822与38710订婚 `material_result=true`，以及玩家29829与接收方32266双向联盟 `allied`；未重复扣款或提案。第4 turn 派生日期 raw `53153976→53154720`，原报告 `elapsed_days=31`。[正式报告](Z:/ck3_mod_rewrite_process_assets/m5-family-r0351-cold-restore-acbc3ed-20260929/run-cold-4/formal-report.txt) SHA-256 `0E78580B20773C1ED499A0B4D2CC3C1DB8E36F249DDEAB407479B5DC6B165037` 为 **4/4 `turn_limit/qualified/ok=true`**、进程树回收。这闭合 R0351 建设/订婚/联盟的**新 PID 原生状态冷读**和后续正式 turn 消费；建筑仍施工中、无完工收益证明。R0351 的 9 天及 R0354 的 31 天均属派生 h90，不计入 Robert 持久天数；G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**和 PRV008 冻结资格不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0355 建设到期观察增量：从 R0354 派生 h112/raw53154720 合法配对新启 PID112500，4/4 正式 turn 再读同一建筑槽 `applied/in_progress`、剩余工作 raw `105,055,560`，订婚和双向联盟仍成立；第4 turn 仅战争入口只读 `query-declarable-wars`，**无新建设/提案或日期推进**。[正式报告](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0354-due-watch-20260929/run-watch-4/formal-report.txt) SHA-256 `AF08A9D61311F7053E928F63899D48E5A85D54DE3412AB594017AD7326BCCA44` 为 `turn_limit/qualified/ok=true`、`date_advanced=false`、进程树回收；末 h117 仍 raw53154720。该轮补充恢复后的持续施工观察，**未完工、无收入增量**；不增加派生或 Robert 游戏日。G2 **3/8**、Robert **3,150/36,524 日**、PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0356 活动只读增量：H3928/raw53219928 新 PID76388 在同一 paused `native:3` 先原生打开 feast planner，再以默认关闭的私有只读口读取阶段1已选 `feast_type_generic`：`selected_option_shown=true`、`selected_option_valid=true`、`can_progress_stage1=true`、`generic_feast_confirm_ready=true`，无指针持久化。[正式报告](Z:/m6-activity-h3928-stage1-read-candidate-v2-20260929/operator-runs/feast-stage1-option-read-1/formal-report.txt) SHA-256 `562B9B2E9A01020CA593746872FFE733B030DBD6D08784E9B3F824305848BCD2` 为 `private_activity_feast_stage1_option_observed/read_only_observed/ok=true`，源/后帧日期均 raw53219928，进程树回收；[候选索引](Z:/m6-activity-h3928-stage1-read-candidate-v2-20260929/CANDIDATE-INDEX.json) SHA-256 `3974E975425FE68E03A735C459CD82DF585D6E373CE7D29D4B97B66608CF05D5`。这证明当前**阶段1选项**可显示、有效且可进入下一规划阶段；尚未按 Confirm、未进入下一阶段，配置费用、最终 CanStart、宴会开始及效果均未知。G2 **3/8**、Robert **3,150/36,524 日**不变。原生证据见[阶段1专题](../ck3-native-ai/activity-planning-stage1-option-identity-1.19.0.6.md)。

09-29 R0357 家庭结果恢复增量：以 R0352 的 H3933/raw53219928 同日配对，在新 PID101676 的一个正式 paused turn 读回 Emma37265→Gerard37267 的原提案仍 `pending/outbound active`、age0/cutoff7、`material_result=false`，并保存同日 h3937/raw53219928 checkpoint；**无重发提案、接受、婚姻或日期推进**。[正式报告](Z:/nw-family-h3933-pending-recovery-v2-20260929/operator-runs/pending-recovery-1/formal-report.txt) SHA-256 `774191FA1A8C37F327E60E56FB11E8572352708BD5A892B64FD4E8200E9D26D9` 为 **1/1 `turn_limit/qualified/ok=true`**、`visible_gameplay=false/date_advanced=false`、进程树回收；h3937 save SHA-256 `92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6`。这闭合纯结果读取的**专用资格/新 PID 恢复**，R0352 原资格 RED 历史保留；提案物质结果及后续状态变化仍待游戏自然推进。Robert 持久高水位仍 **H3911/raw53219928、3,150/36,524 日**，G2 **3/8**、百年/整局/种子 **0/1、0/1、0/2**、PRV008 冻结资格不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0358 派生建设到期观察增量：从 R0355 的 h117/raw53154720 合法配对新启 PID69120，正式 24/24 turn 将派生日期推进至 h161/raw53155704，合计 **41 个派生游戏日**。第1 turn 同槽施工仍 `applied/in_progress`、剩余工作 raw `105,055,560`；先推进31天，再于第5 turn、raw53155464 读同槽仍 `in_progress`、剩余 raw `101,611,119`、完工/玩家收入增量为 null。**这是末次建筑读回**，不能由最终 h161 日期推断建筑已完工或实收。[正式报告](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0355-continuation-73e5540-20260929/run-watch-24/formal-report.txt) SHA-256 `FB74A464AA7EA6C1051EF7D020614A16E3418F484725D53F473F475237C191D7` 为 `turn_limit/qualified/ok=true`、进程树回收；[候选索引](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0355-continuation-73e5540-20260929/CANDIDATE-INDEX.json) SHA-256 `81FF89E773CF24AD793699CFC6336DA4C45FDC38924AB84583137E65BD05EC05`。后续 turn 走派生战争路线，提交宣战、征兵及军队移动并再推进10天；这些是该候选的上下文，战果不在本非战争包验收。没有新建设或婚配提案；41天均不计入 Robert。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、百年/整局/种子 **0/1、0/1、0/2**、PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0359 活动成本原始槽只读增量：H3928/raw53219928 的新 PID16484 在 actor29829 同一 paused 阶段1先打开 `activity_feast` planner，再由默认关闭的私有查询读出 slot12 的 **10 个 raw i64：`[10000000, 0×9]`**；`resource_mapping=null`、`configured_cost=null`，因此 raw 首值**不能**直接记作金币成本、可负担报价或费用承诺。[正式报告](Z:/m6actcostrawh3928v2_20260929/operator-runs/slot12-raw-read-1/formal-report.txt) SHA-256 `30EC3B42D88B51C1007EA9C32E9E4AD200EE267A28D9ECFD918EBA8D9C928E44` 为 `private_activity_cost_slot12_raw_observed/read_only_observed/ok=true`、同帧 date raw53219928、进程树回收；[候选索引](Z:/m6actcostrawh3928v2_20260929/CANDIDATE-INDEX.json) SHA-256 `600777EDF1443FBC7A311491C6B9D33BCC978739FBF3B4B70CDD17C931B8CC27`。本轮只执行 planner 打开和只读观察，**无类别 Confirm、宴会开始、资源扣费或日期增长**，最终 CanStart 仍未知。#588 后续阶段选项原生源码已入 master `d36e97a`；#589 Python 路由 PR 已 CLOSED 且未合入，其 rebase-only 替代 PR #590 已入 master `3e24960`。这些源码交付都没有给 R0359 补一个 live 活动动作，不能计入活动消费。

09-29 R0360 同一 H3928 的私有 Stage1 Confirm 正式尝试为 **RED**：[正式报告](Z:/m6-activity-h3928-confirm-candidate-20260929/operator-runs/feast-stage1-confirm-1/formal-report.txt) SHA-256 `D59B08B4D2514FA6D56EFC495E2EEE15BA1B8ECEF1E19060BBB2DB3244F5C01D`，[候选索引](Z:/m6-activity-h3928-confirm-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `DB56FB20DC04CF17354FA294610FB7C0FC97D961C46137F7211A85961A26E430`。actor29829、date raw53219928 的原生回执观察到 `precondition_status=observed`、`generic_feast_confirm_ready=true`，但最终 `status=precondition_rejected`、`submitted=false`、`pending=false`，阶段2不可见；金币 raw `120644281→120644281`、快照及存档未变。operator `formal_run_failed`、尝试1 turn/成功0 turn、日期增长0，退出后进程树已回收。**预条件观察不等于 Confirm 已提交或宴会已开始**；根因仍待定位，不能将本轮计入活动动作、费用或收益。#596 源码已入 master `1361835`，其静态交付也不改变此实机 RED。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 冻结边界不变；后续仍需合法 Confirm 后置、阶段2及最终 CanStart 实测。

09-29 R0361 同一 H3928 Stage1 Confirm 拒绝原因诊断仍为 **RED**：[正式报告](Z:/m6-activity-h3928-confirm-reason-candidate-20260929/operator-runs/feast-stage1-confirm-reason-1/formal-report.txt) SHA-256 `DAA8B93387EA2C62DB0ACCC387D82D01AE3AA69A75956B14269583AE858159E5`，[候选索引](Z:/m6-activity-h3928-confirm-reason-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `6E78D1F0B1A2B5DFB5B128763D5C587F28C73F023DC5A8D39B84CF99B12EA307`。actor29829、raw53219928 的原生回执再次读到所选 generic 选项有效、`precondition_status=observed`、`generic_feast_confirm_ready=true`，同时把拒绝原因明确读为 `precondition_reject_reason=stage_auto_nonzero`、`planner_stage_auto_raw=1`；最终仍是 `precondition_rejected`、`submitted=false`、`pending=false`、阶段2未读。金币 raw `120644281→120644281`，原始存档 SHA-256 `A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C` 与日期均未变；operator `formal_run_failed`、成功及可见游戏 turn 均为0、进程树回收。该字段**收窄拒绝位置，不表示已修复或已提交 Confirm**；没有宴会开始、费用、收益或 Robert 持久日期增量。G2 **3/8**、Robert **3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 不变。

09-29 R0362 同一 H3928 的私有宴会 Stage1 Confirm 取得**同 paused 帧局部动作后置**：[正式报告](Z:/m6-activity-h3928-stage1-byte1-candidate-20260929/operator-runs/feast-stage1-byte1-confirm-1/formal-report.txt) SHA-256 `F19F6BE7248EE9C5B84F32D5B4CBDD73478D1D3F01121E4B727D508481F2A09B`，[候选索引](Z:/m6-activity-h3928-stage1-byte1-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `8DC53DC58B56061B5A079F7781981A73D3D556D8540FD4E55DBB9A2AE8B119A4`。actor29829、raw53219928 的 `feast_type_generic` Confirm 回执为 `accepted=true`、`submitted=true`、`stage_two_visible=true`、`selected_option_retained=true`，planner 到阶段2；随后私有只读观察读到两条 configuration row 的 `raw_dword` 均为0，`can_progress_stage2=false`。金币 raw `120644281→120644281`、日期及存档未变；报告为 `private_activity_feast_stage2_gate_observed/planning_stage_advanced/ok=true`，进程树回收。**只证明 Stage1 选项提交与阶段2可见**；没有 Stage2 配置或确认、最终 Start、费用/收益、下一 turn 或 cold restore，不能计作完整活动自动游玩闭环。G2 **3/8**、Robert **3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 不变。

09-29 R0363 同一 H3928 的私有宴会继续在 paused 同帧提交 Stage1 `feast_type_generic` Confirm，并读到阶段2的**地点只读候选**：[正式报告](Z:/m6-activity-h3928-stage2-location-candidate-20260929/operator-runs/feast-stage2-location-read-1/formal-report.txt) SHA-256 `FC03139BBED6B784F6E0220A323678BE04C49EC3D0678771491E9EBA45DC5ED0`，[候选索引](Z:/m6-activity-h3928-stage2-location-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `1AC118D61058B9A24C61E9B257AB4287A41818D67C8F87CA29CA281C0CE0CC75`。actor29829、raw53219928 的 Confirm 回执 `submitted=true`、`stage_two_visible=true`、原选项保留；原生地点回执 `read_only=true`，province **2619、2629** 均 `can_select=true`，`active_row_index=0`、`activity_single_location_flag=true`、`previous_planning_stage=1`。两条配置行的 `province_id` 仍为0（第0行 active），`can_progress_stage2=false`；**可选不等于已选**。金币 raw `120644281→120644281`，日期及原存档 SHA-256 `A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C` 未变；operator `private_activity_feast_stage2_location_observed/planning_stage_advanced/ok=true`、成功游戏 turn 为0、进程树回收。没有地点提交、Stage2 Confirm、最终 Start、费用/收益、下一 turn 或动作后新 PID cold restore。G2 **3/8**、Robert **3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 不变。

09-29 R0364 从同一 H3928 配对重新冷启，在 actor29829、raw53219928 的 paused 帧重做 Stage1 Confirm 后，原生判定省份 **2619** 可选，私有 typed 地点动作仅提交一次；[正式报告](Z:/m6-activity-h3928-stage2-destination-candidate-20260929/operator-runs/feast-stage2-destination-2619-1/formal-report.txt) SHA-256 `679E860EC1F4FBBA852CD9BA7BD27A45D1389CF08538485B4DF0B0CC973FA54E`，[候选索引](Z:/m6-activity-h3928-stage2-destination-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `A194B6629B8B24CAC7D179D77E9187F9AEABC81D6EA5ADE3D51F8186F9928ED1`。独立新鲜 planner 读回 `planning_stage=2→5`、两条配置行 `province_id=[0,0]→[2619,2619]`、原选项保留，动作状态 `verified_stage_five/submitted=true/needs_recovery=false`；金币 raw `120644281→120644281`，日期及来源存档未变。operator `private_activity_feast_stage2_destination_selected/planning_stage_advanced/ok=true`，进程树已回收。回执中的 `no_activity_started` 仅表示本有界地点选择分支未调用 Start，规划器仍在 Stage5；**并非独立 hosted activity census**。没有最终 Start、费用/收益、下一 gameplay turn 或动作后新 PID cold restore，不能计作完整 M6 闭环。源码 master `58d6bf8` 的 exact 官方 CI #36544818252 SUCCESS；G2 **3/8**、Robert 持久 **3,150/36,524 日**、长期门 **0/1、0/1、0/2** 与 PRV008 不变。

09-29 R0365 从同一 H3928 配对重新冷启，Stage1 Confirm 与省份 **2619** 的 Stage2 地点选择再次取得独立后置，随后 Stage5 四资源费用/最终 CanStart 私有查询返回 **`native_activity_stage5_full_cost_red:gold_gate_red:exact_build_rejected`**；[正式报告](Z:/m6-activity-h3928-stage5-fourcost-candidate-20260929/operator-runs/feast-stage5-fourcost-read-1/formal-report.txt) SHA-256 `E2466AFEF3573AB843C4C71243D146EA914CA8CB5B009337ED969C5D468CCC5A`，[候选索引](Z:/m6-activity-h3928-stage5-fourcost-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `94B765F73379712EA5FC1B8F9A5681A3500A84BC9E5E2B0D76E7AA98DA71D6EA`。`first_blocker.stage=private_activity_feast_stage5_full_cost_read`、operator `formal_run_failed/exit1`；**没有有效费用或 CanStart 读数，也没有 Start**。金币 raw `120644281`、raw53219928 日期和原存档 SHA-256 `A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C` 未变，进程树已回收。Gold 子查询的 transport enable 接线缺口正在修复；本轮没有新增持久日期、完整活动动作或下一 turn/冷恢复证明。G2 **3/8**、Robert 持久 **3,150/36,524 日**及长期门 **0/1、0/1、0/2** 不变。

09-29 R0366（B 成本/CanStart 有界读）从同一 H3928 配对冷启，在 Stage1 Confirm 与省份 **2619** 的 Stage2 地点动作后，paused Stage5 四资源原生查询 **GREEN**：[正式报告](Z:/m6-activity-h3928-stage5-fixed-r0366-candidate-20260929/operator-runs/feast-stage5-fixed-cost-only-1/formal-report.txt) SHA-256 `7E9885E0F0F17ED0695F5AAC4FC159B602B1B0CD2C42A87B2BDE109A0D48579E`，[B 候选索引](Z:/m6-activity-h3928-stage5-fixed-r0366-candidate-20260929/CANDIDATE-B-INDEX.json) SHA-256 `DB52EBE6A1511B3378BC538EA84ED97B00A26DCEE47549151CBEC5FBEA0DD9B7`。配置费用 Gold `10000000/100000=100`，Treasury、Piety、Barter Goods 均为0；玩家金币 `120644281/100000=1206.44281`，但原生 **`final_can_start=false`**，不能仅由金币可负担推断 Start 合法，否决原因仍待观察。R0365 的 Gold 查询 RED 在此候选已消除；本轮只读费用/最终判定，**未调用 Start**，没有费用扣除、活动成立、收益、下一 gameplay turn 或 cold restore。operator `private_activity_feast_stage5_full_cost_observed/planning_stage_advanced/ok=true`，raw53219928 日期与原存档未变，进程树回收。G2 **3/8**、Robert 持久 **3,150/36,524 日**及长期门 **0/1、0/1、0/2** 不变。

09-29 R0367（A Stage5 输入只读）使用同一 H3928 配对，在新 PID 的 paused 帧重做 Stage1 Confirm 与省份 **2619** 地点选择后，四项配置费用仍为 Gold **100**、其余 **0**，原生 `final_can_start=false`；[正式报告](Z:/m6-activity-h3928-stage5-fixed-r0366-candidate-20260929/operator-runs/feast-stage5-fixed-cost-input-read-1/formal-report.txt) SHA-256 `35C04DD2B42619442D98D3A6EA5AD48DAD5868CE7DA71E9D55A68F79903CE486`，[A 候选索引](Z:/m6-activity-h3928-stage5-fixed-r0366-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `BFE32888F306DF5B402EF334E384A341644283D71C82C0EF7FC5BBE6EA5E19CB`。输入读口报告 `hosted_activities=[]`，但 `guest_join_status=planner_unavailable`，`selected_nonhost_count`、`positive_join_count`、`timely_positive_join_count` 均为 `null` 且 `arrival_time_observed=false`；**不能把未知宾客数写成0，也不能据此归因 CanStart 拒绝**。策略 `decision=hold/decision_reason=native_final_start_unavailable`，未提交 Start，尚无活动、扣费、收益、下一 gameplay turn 或 cold restore。operator `private_activity_feast_stage5_start_assessed/planning_stage_advanced/ok=true`，raw53219928 日期与源存档未变，进程树回收；G2 **3/8**、Robert 持久 **3,150/36,524 日**及长期门 **0/1、0/1、0/2** 不变。

09-29 R0368 同一 H3928 配对的 paused Stage5 读口再次得到 Gold 费用 **100**、其余三项 **0**，`final_can_start=false`；[正式报告](Z:/m6-activity-h3928-stage5-gap-candidate-20260929/operator-runs/feast-stage5-guest-failure-read-1/formal-report.txt) SHA-256 `883CC43B513CE7F01A18A61DB27ACCA923F2F3D781F5836306AC0B7FCEE39EB6`，[候选索引](Z:/m6-activity-h3928-stage5-gap-candidate-20260929/CANDIDATE-INDEX.json) SHA-256 `E7A3B2AACBA9DD26ECD2018E561164D9F6789047D68FE10AD1BF629968FDA039`。原生 `final_can_start_failure_display.state=known`，显示文案包含“你不能在军队中担任将领或骑士”；它是本帧本地化**显示文本，不是稳定原因 key**，不能据此断言具体军队职务或解除方法。宾客读口这次 `guest_join_status=observed`、`selected_nonhost_count=0`、`positive_join_count=0`、`timely_positive_join_count=0`、`arrival_time_observed=true`；与 R0367 的未知数值分开记账。策略保持 `decision=hold`，**没有 Start**、费用扣除、活动成立或下一 gameplay turn；operator exit0/ok=true，raw53219928 日期和源存档未变，进程树已回收。G2 **3/8**、Robert 持久 **3,150/36,524 日**、百年/整局/双种子门 **0/1、0/1、0/2** 不变。

09-29 R0369 派生建设冷恢复与到期观察增量：从 R0358 h161/raw53155704 的合法 save/driver/sidecar 配对，以新 PID183884 和官方 no-launch `ready` 候选最小化运行，正式 **48/48 turn 成功、14 visible gameplay turn**，最终 h272/raw53155968，新增 **11 个派生游戏日**。[候选索引](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0358-continuation-a2ff7f1-20260929/CANDIDATE-INDEX.json) SHA-256 `445BEE391A40E1A2C490677BCAB0790F6CBAEC3B006BAA67EAE8A851989EB9D5`，Python 来源 master `a2ff7f1675d78eaa4712c0dbf3e41a1c9af31877`（exact CI #36558952374 SUCCESS），所用原生 DLL SHA-256 `9F4811298706D062BC9AEDFA8B39BCB057D6D19C3B836C889A6971619F6B6D77` 来自 `b495b0f`，相关原生建设接口增量为空。首 turn 新 PID 原生读到同一 `hill_farms_01`、barony2174/province2629/slot1 仍 `applied/in_progress`，剩余工作 raw `101611119→100500009`，该省月收入 raw `87000→87000`；最终日期后的建筑状态**未再读**，下一次按原有 720 raw 间隔的检查门为 raw53156424，不能由日期或预测收益推断完工。第2–3 turn 冷读继承人38822与38710订婚、玩家29829与接收方32266双向联盟 `allied`，没有重复提案。第8–9 turn 正式查询并选择一个已显示且可点的单选模态事件选项，独立读回事件 instance4→none；选择政策为 `forced_presentation`、`semantic_decision_ready=false`，同帧压力、金币、威望不变，其他效果未独立观测。此处新增**阻塞事件的实际消费**与派生建设/家庭恢复可靠性，不是新建筑开工或效果收益。[正式报告](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0358-continuation-a2ff7f1-20260929/run-watch-48/formal-report.txt) SHA-256 `1EB63CBC83406780462726E0E9CE31D56D7F58DA808592519DAEE930CD15B77C` 为 `turn_limit/qualified/ok=true`、`first_blocker=null`；[operator 回执](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0358-continuation-a2ff7f1-20260929/run-watch-48/operator-receipt.json) SHA-256 `C91FFE91DE40F9A1EB14C341313CE902A7530A94D92FBB3F335BA95DC1B20277` 为 completed/exit0，末 checkpoint save SHA-256 `7FD9852A96D7FFA11DC6227813C35C3120D05E7CECA21FD0903F15584BF59B3D`、h272，进程树回收。**这 11 天不计入 Robert 正式持久日期**；G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、百年/整局/种子 **0/1、0/1、0/2** 与 PRV008 资格不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0370 派生建设续跑与恢复计时缺口：从 R0369 h272/raw53155968 的合法配对，以新 PID181636 最小化后台运行，正式 **112/112 turn 成功、32 visible gameplay turn**，末 h536/raw53156640，增加 **28 个派生游戏日**。[候选索引](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0369-continuation-3ed73d6-20260929/CANDIDATE-INDEX.json) SHA-256 `0EEBC7832C1E33F6039DE73AF41F7EC298DF9EBC1E0F9A5FA5C703D9AEA8388C`，来源 exact master `3ed73d6d3681cbec25ec350f78788454c6b0c17d`、官方 CI #36561147150 SUCCESS，原生 DLL SHA-256 `9F4811298706D062BC9AEDFA8B39BCB057D6D19C3B836C889A6971619F6B6D77`；后续 master `cfe8ae7` 的相关增量仅是进度文档，未热换 live。首 turn 冷读同一 `hill_farms_01`、barony2174/province2629/slot1 仍 `applied/in_progress`，剩余工作 raw `100500009→99277788`、省月收入 raw87000 未变；第2–3 turn 再读继承人38822与38710订婚、玩家29829与接收方32266双向联盟 `allied`，未重复施工或提案。**首 turn 的无条件恢复复查把 `completion_last_check_date_raw` 从 53155704 重置为 53155968**，使原计划 raw53156424 的施工复查推迟到 raw53156688；本轮虽推进到 raw53156640，仍差 **2 游戏日**，因此最后日期没有新的建筑状态或收益读回。这是已观测的恢复计时饥饿缺口，修复在独立包进行，不能把长跑或预测收入当作完工证明。[正式报告](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0369-continuation-3ed73d6-20260929/run-watch-112/formal-report.txt) SHA-256 `C445367DB258F0D80DCCBF2C3E257233651645CEA5D6152392D6453B14A66342` 为 `turn_limit/qualified/ok=true`、`first_blocker=null`；[operator 回执](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0369-continuation-3ed73d6-20260929/run-watch-112/operator-receipt.json) SHA-256 `B864D58CDCE213A79228661447F2AFB5F875CBD03FFA54FC5A3743D5602AC783` 为 completed/exit0，末 checkpoint save SHA-256 `E2B52CE46C9F59222F1022D3B33266A3570C34A54BEC1116CA6EAEC1426FD022`，进程树回收。**本轮没有新非战争提交或完工收益，28 个派生日不计 Robert**；G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、百年/整局/种子 **0/1、0/1、0/2** 与 PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0371 活动宾客候选实机读口 **RED**：从 H3928/raw53219928 原始合法配对新启 PID187676，在 paused 同帧重复已验证的 Stage1 Confirm、ProvinceID2619 地点选择与 Stage5 四费用读回（Gold100、其余0、`final_can_start=false`），再调用默认关闭的私有普通宾客候选查询。[候选索引](Z:/m6-activity-h3928-stage5-ordinary-guest-prep-20260929/CANDIDATE-INDEX.json) SHA-256 `F18144B355FF66044E78DDFA99D85F425BF0B398D7DE11291CB534B3D2D9AEA8`，来源 exact master `3ed73d6d3681cbec25ec350f78788454c6b0c17d`、官方 CI #36561147150 SUCCESS，DLL SHA-256 `2E45D9E10735B0F25E861661966B8DCE209E0BC53BF0D0719DD8D1B2D38B19BD`，官方配对/no-launch ready。原生 `candidate_read.status=exact_build_rejected`，`normal_refresh_sequence/source_fingerprint/native_filtered_pre_invitation/candidate` 均 null；**既非候选已观测，也非完整枚举后的真实空集**。外层报告误列 `ok=true/first_blocker=null` 和 operator exit0，不能覆盖内层 RED；正式 `auto_run` attempted/successful/visible turn 均0、日期及原始 save SHA-256 `A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C` 不变，窗口最小化后进程树回收，未邀请宾客、未 Start。[正式报告](Z:/m6-activity-h3928-stage5-ordinary-guest-prep-20260929/operator-runs/feast-stage5-ordinary-guest-candidate-read-1/formal-report.txt) SHA-256 `30BBADD71B34C0A76B0DE8B8EE70DDEED40EEAA12D749E0D39F9288CA5FCFF79`；[operator 回执](Z:/m6-activity-h3928-stage5-ordinary-guest-prep-20260929/operator-runs/feast-stage5-ordinary-guest-candidate-read-1/operator-receipt.json) SHA-256 `37C237E44E2F1A0469D7839E4C6FD708660217D70E711E99E2197AE17E473AA4`。exact-build 源码定位 VerifyAbi 在 `0x151CD6E` 校验了下一条指令字节，实际目标始于 `0x151CD75`；#654 Python RED 传播已合入 master `3a15170`、官方 CI #36565548462 SUCCESS，#655 原生修复已合入 master `4df75c3`、官方 CI #36566040969 SUCCESS，**两者均无修复后 live 证明**。下一步以修正制品与新 PID 重做原生候选读，只有真实 `observed` 或完整枚举后的 `no_qualified_candidate` 才能收窄宾客机会；R0371 不能计活动消费。G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、百年/整局/种子 **0/1、0/1、0/2** 与 PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

09-29 R0372 建设冷恢复到期读回：从 R0370 派生 h536/raw53156640 合法配对新启最小化 PID134488，正式 **32/32 turn 成功、9 visible gameplay turn**，末 h604/raw53156784，新增 **6 个派生游戏日**。[候选索引](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0370-coldwatch-715279f-20260929/CANDIDATE-INDEX.json) SHA-256 `3FF6A924F97891107E024BA64A233E6C2911071F175AE72D149DFAEE18E417CD`，来源 exact master `715279fd9cd807d41c253c72e496a6fa9f0c0f2b`、官方 CI #36564503870 SUCCESS，原生 DLL SHA-256 `9F4811298706D062BC9AEDFA8B39BCB057D6D19C3B836C889A6971619F6B6D77`。[#651](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/651) 的恢复计时修复在本候选源码中：第1 turn 新 PID 冷复查于 raw53156640 读同一 `hill_farms_01` barony2174/province2629/slot1 仍 `applied/in_progress`、剩余工作 raw `96166680`，**没有把既有 `completion_last_check_date_raw=53155968` 重置**；第18 turn 正好在原定 raw53156688 再次独立原生查询同槽，仍 `in_progress`、剩余 raw `95944458`，此时才把 last_check 更新为 53156688，省月收入 raw87000 未变。这证明恢复后的到期复查真实触发，修复的窄范围 live 恢复缺口；建筑仍未完工、未证明兑现收益。[正式报告](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0370-coldwatch-715279f-20260929/run-coldwatch-32/formal-report.txt) SHA-256 `6B1CBAB1CD7108CB72794ED7F828A7C635F1521CA44D7139B81FFA2096AC51D4` 为 `turn_limit/qualified/ok=true`、`first_blocker=null`；[operator 回执](Z:/ck3_mod_rewrite_process_assets/nw-econ-r0370-coldwatch-715279f-20260929/run-coldwatch-32/operator-receipt.json) SHA-256 `8A2AEA5B199C1716204DF2AE74B9CB114EFE471997D684C49C89B07B441CD8DA` 为 completed/exit0，末 h604 checkpoint save SHA-256 `5E43DEA244C3869E09EC4C8B15FF7646680C4A2670267C1040B0E6ED8144CAF8`、树回收。**6 个派生游戏日不计 Robert**；G2 **3/8**、Robert **H3911/raw53219928、3,150/36,524 日**、百年/整局/种子 **0/1、0/1、0/2** 与 PRV008 不变。详见[09-29 日报](daily/2026-09-29.md)。

### 2026-09-29 当前执行状态

- G2 固定完成数 **3/8**：M0、M1、M3 complete；M2、M4 in progress；M5–M7 not started。局部动作或只读能力不自动改变里程碑状态。
- 正式 Robert 最近可恢复持久配对为 **h3911/raw53219928、3,150/36,524 游戏日**；百年门 **0/1**、首整局 **0/1**、独立种子 **0/2**。派生 h90 日期不计入 Robert。R0321 从 h3860 继续，前 26/27 turn 成功，持久 **+6 日**；第 27 turn 因战争接触同帧 forecast producer `unavailable`、encounter scope 不匹配而阻断，**0 新非战争动作**，整轮仍为 RED，不提升 G2 里程碑。正式报告 `Z:\ck3_mod_rewrite\.task-tmp\M7-ROBERT-H3860-a6d1\run-formal-36\formal-report.txt` SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30`；H3911 save SHA-256 `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`、源 driver SHA-256 `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`，配对身份 SHA-256 `FDE4CC3A64DF5BB5D83F7B132FE5CC2985D31ACA28F0883A1C6245C197B5915E`、官方 no-launch 报告 SHA-256 `1067E8468BE61A6B0240E12B145FD173D6DCD4E786FED3991E7E436253E75712` 为 `ready`。R0319 的 36/36 合格结果仍见[日报](daily/2026-09-28.md)。
- R0311–R0313 的囚犯 47028 私有 `current_gold` 路线已有一次 typed 提交、实际 **7 金**与释放、下一正式查询及新 PID 冷恢复的窄范围闭环；公共 M6 query/action/ad 与完整 M6 仍未开放。Emma 的旧 `not_player_child` 读数已由 #504 的原生 `is_child_of` 预门替换；R0323 同帧读到真实亲子与默认五角色 Can Send/最终答复阳性。#508/R0324 读到 Emma37265 与 Gerard37267 的默认婚配母系未生效，政策不提交；#510/R0325 读到 `selected=true` 的母系选项最终 Can Send/答复阳性且若接受可成婚。R0324/R0325 均是**只读、0 动作/日期**，唯一潜在联盟 pair 的 `would_attempt_if_accepted=false`。R0328 对该 subject-bound 选项完成一次私有 typed 提交，native ACK accepted、持久 ledger `receipt_pending`；#515 完成 child sidecar 复制接线。R0329 新 PID 原生读到提案 `pending/outbound active`、无重复提交，随后战终查询恢复；第三步安全截停造成 wrapper `cold_result_not_qualified` 分类 RED。R0352 再读该 Robert 提案仍 pending，资格外层 RED 保留；R0357 新 PID 又读 pending，并通过结果专用资格，**Robert 这笔婚姻、联盟及日期推进仍未发生**。另有 R0351 派生 h90 场景实际订婚与联盟，R0354 新 PID 冷读已证实，仍不提升完整家庭门。详见[09-29 日报](daily/2026-09-29.md)。
- 当前非战争执行顺序为 **NW-LIFE → NW-ECON → NW-FAMILY**，**NW-JOINT** 同帧资源分配并行接线。R0321 多帧生活方式机会复核均为有效财富 focus、未用点数 **0**，无可证明漏消费；R0326 在 Robert 战时同帧读到合法且预计增收的空槽农庄，但 M5 战争现金七字段缺项、`cost_ready/action_ready=false`，未开工或实收；#505 的 `selected_step=null` 修复分支在该帧未走到。R0351 在**独立派生 h90** 用正式 M5 选择器开工一项农庄，并选出继承人订婚且读到实际双向联盟；R0354 新 PID 又读回三项状态且继续正式 turn，R0370 新 PID 冷读仍见同槽施工中、订婚与双向联盟保持，派生再推进 28 天，但恢复复查重置到期门且未读到完工收益，不能外推到 Robert 战时现金比较。Emma 母系选项已提交且待物质后置及恢复，不能从 ACK 推断已婚；R0327 派系只读在当前窄政策下无直属有地成员赠礼目标，未进入成本/合法动作。联合比较不能把战争现金缺项当零。战争研究由维护者负责，非战争执行者只消费已交付入口。PRV008 冻结资格与这些新候选分开。

## 口径纠正

G2 的终点是能够跨继承、跨玩法域持续完成“观察 → 决策 → 操作 → 验证”的 CK3 玩家智能体。历史上的 fixed-seed
`start-next-episode` 和第二寿命证明了进程接管、恢复与 episode 生命周期；它们不等于普通 campaign 的真实继承，也不等于
整套玩法覆盖。

G2 采用固定的 **8 个可见 OODA 里程碑**，截至本页状态摘要为 **3/8 complete**。以后只汇报 `完成里程碑/8`、当前里程碑及其子包，
不再汇报没有固定分母的“G2 90%”。旧 `T1=90%` 只曾表示 GEN-034 这个窄战争退出包接近当时定义的收口，且随着真实证据
改写了剩余输入，它已失去可比性。

| 里程碑 | 合同优先级 | 2026-09-29 状态 | 可见验收结果 |
|---|---:|---|---|
| G2-M0 GEN-034 三路战争退出 | P0 | complete | 同帧比较继续、白和、投降；只提交一次；验证战后并冷恢复 |
| G2-M1 实体发现与 core turn bundle | P1-A | complete | 一次聚合查询提供人物、头衔、首都、领主/封臣、邻居与最低 ruler/realm/succession alerts |
| G2-M2 自然事件语义闭环 | P1-B | in progress | 三个自然事件按目标评分并验证结果，至少两个为多选 |
| G2-M3 继承与 realm survival | P1-C | complete | 死前预测逐头衔分配，死后对账并由真实继承人继续 |
| G2-M4 和平治理纵向切片 | P1-D | in progress | 两年内完成并验证建设、内阁调整和一次封臣/派系处理 |
| G2-M5 家庭、外交与完整战争 | P2 | not started | 比较至少五个候选，执行一条从机会选择到最终后置的完整路径 |
| G2-M6 谋略、制度与活动 | P3 | not started | 谋略、囚犯/制度、非宗教决议/法律与活动各完成一个 OODA |
| G2-M7 身份适配与长期整局 | P4-P5 | not started | 跨 ruler/seed/government 资格矩阵及 checkpoint/继承后的高层目标恢复 |

只有一项 query 或一个 fixture 时，状态仍按 `research`、`static-ready`、`fixture-live`、`production-live primitive`、
`production-live loop` 与 `complete` 的既有词汇记录；它不会增加 8 项完成数。每个里程碑必须具备 `latest_evidence`、
`planner_consumer` 和 `visible_outcome`，三者由机器可读文件固定。`py tools/validate_g2_requirements.py` 校验固定 8 项分母、
当前完成数、状态词汇与 GEN-034 子包计数；需求或进度修改后必须运行一次。

以下 GEN-034 与各域施工段落保留原写作时点的研究和证据；段内“当前”“现行”及 `2/8` 等数字描述的是**当时状态**，不覆盖上方日期摘要、里程碑表和机器合同。

## 历史执行记录：GEN-034（M0 已完成）

GEN-034 在 R0043 后为 **4/4 子包完成**。R459 已真实提交一次 surrender，证明 source-specific
`3000→0`、persisted truce expiry `53227656` 与战后生命周期；R471 已在同一 paused frame 两次读取玩家
`13075500000`、对手 `16770900000` 的 strategic power，原生 ratio 为 `128262/100000`。

当时四包为：

1. `GEN-034-A`（**complete**）：把 R471 strategic-power 原语接成 policy-level campaign dominance certificate；
2. `GEN-034-B`（**complete**）：提供有版本、来源、仓库默认值和显式 operator override 的 strategy budget/profile；
3. `GEN-034-C`（**complete**）：在同一 paused frame 取得 white-peace terms 与 utility comparison；
4. `GEN-034-D`（**complete**）：三路 recommendation → 一次 semantic action → WarID/loss/truce/resources 后置 → checkpoint/cold restore。

旧的 index `9/10`、root shape 与 Truce vtable 枚举已被后续证据淘汰。不得再以它们作为当前入口。source attribution、
pre/loss、实际 expiry 和 active-war strategic power 已有证据，不得重复跑这些已关闭的单字段场景。

`GEN-034-B` 已由 `strategies/raiktor_exit_budget_v1.json` 与通用 provider/CLI 闭合：仓库默认 profile 为 `1.0.0`，完整
operator override 必须绑定默认 profile ID/version，实际输入按源文件 SHA-256 绑定。GREEN 离线收据为
`Z:\ck3_mod_rewrite\_runtime\g2-gen034-strategy-profile-20260912\repository-default-profile.json`，SHA-256
`BB20D87233DF6C854DD668FD1641AE590DFFA3BD87CF82099A1A97EBF20C7981`；它只提供策略参数，不提供 campaign 或 white-peace
观测，也不授权 action。

`GEN-034-A` 已由 `raiktor_campaign_dominance_provider.py` 和 hash-bound CLI 闭合。R471 receipt 为
`Z:\ck3_mod_rewrite\_runtime\g2-gen034-a-campaign-dominance-20260912\r471-certificate.json`，SHA-256
`AB0DB5678F65631D63E5A54BA66B61A6F5956179C0A4D3970B78BEAC5E9E0569`。它只发布实测兵力关系；campaign forecast、exit utility、
recommendation 与 action 均保持关闭。该旧 A 包本身不授权动作；C/D 的动作授权与结果由 R0043 的完整生产闭环单独证明。

`GEN-034-D` 已补齐通用 `played_character_prestige` paused-snapshot 字段，复用条款 reader 的 exact-build
`extension+0x130` leaf。这样旧 WarID 消失后仍能比较冻结的 attacker prestige 余额与预期 delta。该字段目前仅
`static-ready / live=false`；它不证明动作、delta、truce、loss 或 cold restore。

recommendation certificate 已把 D 的后置门冻结成可执行数据：玩家 gold/prestige 的前值、selected delta 和精确后值，
以及 WarID、对手、truce days、destroyed cleanup 与 cold-restore 要求。正式 D 门严格采用本页定义的
`WarID/loss/truce/resources -> checkpoint/cold restore`；claims、prisoners、favor 继续参与决策效用，但不额外扩大
里程碑后置范围。

纯函数 `raiktor_three_way_exit_postcondition.py` 已把这六项数据接到现有结果形态：动作 ACK 只验证授权 literal 的一次提交；
同一热会话的后继 paused snapshot 独立核对旧 WarID、gold 和 prestige；action-bound 战后证据核对 source-specific cleanup 与
方向性 persisted truce 的精确天数/到期日；原生 `save-checkpoint`、`restore-checkpoint` 和冷启动后 snapshot 再核对 SHA、替换 PID、
角色、episode、日期、资源及 WarID 缺失。六项全部成立才允许 `gen034_closed=true`。continue 路线只核对 successor revision、
日期、同一战事和角色，永远不关闭 GEN-034。该合同为 `static-ready / live=false`，普通和 optimized 聚焦套件各 `20/20` GREEN；
它没有新增 MCP/native schema，也没有执行 CK3。

### R0043 GEN-034-D production closure

R0043 在 exact CK3 `1.19.0.6` 的同一 paused frame `native:50/revision 51/date 53190816` 比较 continue、white peace 与
surrender；正式策略选择并仅提交一次 `surrender-war-16777285`。独立后帧确认 WarID 消失、gold
`65753016→43253016`、prestige `233114400→133114400`、玩家 `29829` 指向对手 `35991` 的 1825 日 persisted truce
（expiry `53234616`）以及全部 24 个 source-bound regiment destroyed。h1993 checkpoint SHA-256 为
`A89BCF2642E0136B6624AC42F76BDC2314FA01427B3EC62B64A51FBFCBDFB296`；h1994 将 PID `77580→41264` 真冷恢复，h1995/h1996
由正式下一循环消费恢复后的和平状态并解散残军，surrender replay 为零。outer/native report SHA-256 分别为
`9294D8B8D6F8B5485FB69A3B0E1C0E5AAC8F13F6D5D7FB996D3160DC890513EE` 与
`2B726601160586AEEF71E4204441EDD13D50C697F6EAF6975514E68DA5AC82D6`。因此 GEN-034 A-D 为 `4/4`，G2-M0 为
`complete`，固定 G2 完成数为 `2/8`。

## GEN-034 后的历史施工顺序

GEN-034 关闭后立即转向公共 P1，不再继续横向扩展单一 CB 的 ABI：

1. `entity-directory-v1` 与 `ck3_query_turn_bundle_v1` 的 current-feudal-ruler 最小切片；
2. `event-context-v2` 与 registry-driven natural event policy；
3. `succession-state-v1`、health/stress/legitimacy 与 vassal/faction alert 组成的 realm survival；
4. 建设、内阁与派系处理组成的和平治理 OODA。

G2-M1 的前两个 native 子包已达到 `static-ready / live=false`：既有 `campaign-root-context-v1` 现在在同一 paused
application-main 双采样中发布 `direct_landed_vassal_character_ids` 和
`adjacent_external_province_holder_character_ids`。前者枚举 alive、landed 且 immediate liege 为玩家的完整 generation
CharacterID；后者从 exact Province array/native holder/adjacency rows 出发，以“immediate-liege 链是否到达玩家”区分玩家子领地，
再发布边界外直接相邻 Province holder 的升序去重 ID。两项都不借用离线 save topology；Release DLL、native
reader/source-contract 与 Python normal/optimized 聚焦测试均 GREEN。

其上的 canonical relationship-search 切片也已达到 `static-ready / live=false`。独立只读 MCP 工具
`ck3_search_entities_v1` 只消费一次现有 campaign-root query，以 relation filter 和 keyset pagination 返回 self、直属有地封臣和
相邻外部 Province holder 的稳定 CharacterID。新增 `related_character_contexts` 在同一双采样中逐 ID 发布 native primary title、
合法可空 capital、immediate/top liege 与 independent；相邻 holder 保留 source role，再按 top liege 归一 realm identity。
entity-directory 的当前 title/realm components 因而已完整。`ck3_query_turn_bundle_v1` 已聚合最低 ruler/realm/succession alerts、
玩家完整月收入、exact-build health 和 domain size/limit，`ruler_resources_ready`、`ruler_health_alert_ready` 与
`realm_domain_ready` 都由真实输入变绿。逐头衔 partition 与 typed council 也已接入同一 root/bundle。

新轮次 R639 在同一 managed PID、同一 connection generation 和冻结日期上完成独立 ruler `29829` 与 vassal ruler `36108`
两场景：两个 root 和两个 turn bundle 均 `available/ready=true`，两个场景分别发布 8/9 个直属有地封臣、6/15 个相邻外部
Province holder、14/24 个 related contexts，并各自观测 6 个 occupied council task。源存档未变，进程树清理成立。Artifact
SHA-256 为 `CFF681146A344AE18FDEB36C20BDAEAFC2A30344023CC7827E9A77006C3530DB`。G2-M1 因此为 `complete`，固定 G2
完成数提升到 `1/8`；更深派系身份/力量/期限和不同 rank/government/landless 矩阵继续进入各自后续里程碑，不重开 M1。

## G2-M2 离线 direct-projection consumer

机器由人工占用、禁止启动 CK3 期间，M2 的非冲突静态子包已先行完成。`vanilla_events/policy.py` 现在把 shared
exact-build registry 接入 `one-life-turn-v1`：当同帧 event key、玩家 root、saved scopes、snapshot/rendered option count、
native index 与 enabled 投影全部匹配时，planner 采用登记的 source-reviewed bounded continuation。当前真实阻点
`tgp_travel_events.0030` 因此会选择 authored 2/native 1，而不再被通用最小索引 fallback 导向随机学习对决。

已登记 key 若投影漂移、目标选项 disabled，或合同需要尚未实现的人物关系、scope/option variant、动态 native prefix、occurrence 上限、延后选择或场景失效
语义，planner 返回 `active_event_registry_contract_blocked` 并保持不输入；未知 key 才继续旧 degraded fallback。该子包为
`static-ready / live=false`，普通与 optimized 聚焦测试各 `30/30` GREEN。它没有改变 current-window、registry 或 MCP 公共 schema，
没有独立完成 M2；当前固定总进度 `2/8` 来自 M0 与 M1。M2 仍需 variant-aware consumer、event-context-v2 结构化效果、campaign objective 评分，以及三个
自然事件（至少两个多选）的动作与物质状态后置实机证据。

为关闭其中一个真实后置缺口，通用 native state snapshot 已在 `played_character` 上增加可选 `stress_points`。它复用
战争退出资源读取器已使用的 exact-build `CCharacter+0x1A8 -> extension+0x2F8` 路径，不新建另一套 mailbox/MCP。
主 DLL、native fixture 与 Python 正常/异常合同均 GREEN；旧 snapshot 不带字段时仍兼容。registry consumer 现在仅对
`.0030` authored option 2/native 1 绑定同帧角色、snapshot/revision 和选择前压力。native action 复用已经捕获的前后 paused
snapshot，service 输出 `verified_change`、`verified_no_change`、`failed` 或 `unavailable`；压力上升、角色漂移或 ready 合同缺少
动作后读数都会让 auto-run 保持 RED。若选择前压力已经为零，该次安全关闭不会计入 material-delta。

该链仍为 `static-ready / live=false`。下一次允许实机时只需一次有界 `.0030` 复核，同时完成字段 paused read 与 comparator
production proof，不为单事件扩成长跑矩阵。详见
[`played-character-stress.md`](../ck3-native-ai/played-character-stress.md)。

首个 option-variant consumer 也已按真实 R374 阻点收口。`natural_disaster.7031` 的 exact source 和冻结 live frame 证明 native 2
在单选 `[2]`、实际 R374 的 `[0,2]` 与完整 `[0,1,2]` 三种投影中都存在，且只显示 warning tooltip。policy 现在先把当前
option projection 精确匹配到登记 variant，再进入既有 scope/enable 检查；`[0,1]` 等未登记投影继续 blocked。准入目前只限该
event key，其他带 `option_variants` 的合同仍返回 `registered_contract_requires_extended_consumer`，避免一次静态改动暗中扩大事件面。
聚焦测试 normal/optimized 各 `8/8` GREEN；状态为 `static-ready / live=false`。

第二个扩展消费切片来自 R647 的真实 `chancellor_task.1104` 中断。共享合同现已显式冻结五个 saved-scope 名称和
Character 类型、native `[0]` 投影，并由直接策略验证 exact player binding、非玩家排除、官员角色 alias 以及邻国角色
distinct 关系。准入只开放给该 exact-build、source-reviewed event key；关系缺失、身份不可读、alias 漂移或 distinct 漂移均
返回 `registered_contract_projection_drift`，不选择选项。普通与 optimized 聚焦测试各 `24 passed / 200 subtests`；将 R647
真实 MCP 上下文离线重放到消费器得到 `recommended / option 1 / native 0 / failed_checks=[]`。状态为
`static-ready / production-context-replayed`，尚待从未决 checkpoint 做一次真实选择与后置观测。

两条已进入 planner 的选择现在还带有机器可读的 `xar.ck3.vanilla-event-choice-effect` 档案。`.0030` 记录 authored
`medium_stress_impact_loss = -30`，同时明确 `runtime_delta_exact=false`，因为人物压力影响修正尚未观测；其 comparator 从同一档案读取
`played_character.stress_points / non_increasing`，不再另写一份效果假设。`natural_disaster.7031` 则区分 selected native 2 的纯
warning tooltip 与所有选项之后必经的 character variable 写入，并把后者标为当前不可观测。两条档案都由既有只读
`ck3_query_vanilla_event_knowledge_v1.analysis` 对外查询，policy 只在 exact native choice 对齐时返回副本。

这项能力是 `source-structured / static-ready / live=false`，只覆盖两条 exact source-reviewed 选择；它没有实现通用
`event-context-v2` effect visitor，也没有把未观测的 runtime magnitude 或 common-after variable 冒充为 live 后置证据。普通与
optimized 聚焦测试各 `27/27` GREEN。

第二条 material comparator 现覆盖 R414 的 `trait_specific.8001`。authored option 2/native 1 的 effect profile 记录
`add_gold = minor_gold_value`，但由于原版动态值依赖月收入、treasury 与 era，只承诺 Q100000
`played_character_gold.raw / strictly_increasing`，不预报精确 delta。native state snapshot 复用既有 exact-build
`extension+0x100` 金币 leaf；planner、action 与 service 绑定同一 CharacterID 和选择前 snapshot/revision，只有动作后 raw 严格增加
才算 material change。不变、下降、身份漂移或缺读数保持失败/不可用。

主 DLL 与 native fixture GREEN，Python normal/optimized 聚焦测试各 `30/30` GREEN；状态仍为 `static-ready / live=false`。
`.0030` 与 `.8001` 各只待一次 bounded live action 证明，不为任一单事件启动长跑。连同下述第三条静态路径，G2-M2 仍需
campaign objective 评分与三个 production event loops；当前固定总进度为 `2/8`。详见
[`played-character-gold.md`](../ck3-native-ai/played-character-gold.md)。

第三条静态 material path 现选定已有真实证据的 `death_management.1007`。R374 已证明唯一 authored1/native0 的 event instance
advance；本包为该 key 精确消费 distinct `dead_character` scope，发布 authored `minor_stress_impact_gain = +20` 档案，并复用
玩家压力字段验证 `non_decreasing`。正向 delta 才计 material evidence；压力封顶导致的不变被记录为非 material，反向下降或身份漂移
不能通过。其它 unique-exclude 合同仍 blocked。

该 comparator 为 `static-ready / live=false`。R374 的旧 hot park 没有 durable checkpoint，不能冒充可冷恢复输入；今后只在正常
campaign 自然再遇时顺手做一次 bounded 前后对账，不为 `.1007` 单独长跑。至此三个目标事件均已有静态 material comparator，但
三条 production material loops 与跨事件 campaign objective 评分仍未闭合，所以 G2-M2 继续 in progress；当前总进度为 `2/8`。
详见 [`heir-death-stress.md`](../ck3-native-ai/heir-death-stress.md)。

三个目标事件的 bounded campaign objective/utility 输入也已 static-ready。每个 analysis record 现发布 versioned ordinal profile；
policy 只在 exact native choice 对齐时复制，`one-life-turn-v1` 把它写入 `event_campaign_utility`。`.0030` 以“减压且不延误旅程”
为目标，`.8001` 以“增加流动金币且不引入随机持久状态”为目标，两者都将 native1 排为当前首选；`.1007` 则诚实记录唯一合法路线
及其不可避免的压力成本。planner 因此不再只写“bounded continuation”，而是保存 objective、selected rank、utility 特征和替代原因。

该评分为 source-reviewed ordinal，不是跨域数值模型：`cross_event_numeric_score=null`、`calibration_status=not_calibrated`、
`semantic_optimal=false`。它关闭三个 exact 事件的最小静态“目标和 utility”输入；实时压力/财政/继承风险驱动的动态目标切换、通用
event-context-v2 effect visitor 与更多事件仍是扩展债，不再作为这三个事件 live loop 的前置。聚焦测试 normal/optimized 各
`26/26` GREEN，详见 [`event-campaign-utility.md`](../ck3-native-ai/event-campaign-utility.md)。

战争 controller 的既有成熟执行器继续保留；assigned reinforcement、terminal 长尾与更多 CB 改为真实 encounter 驱动。
宗教域继续暂缓，只允许战争中的圣战和婚姻合法性/接受度所需的最小原生最终判定，不借此扩展通用宗教模型。

## 报告规则

- 总进度只写 `G2-Mx / 8`，2026-09-28 状态为 `3/8`；
- 活跃工作包另写 `完成子包/总子包`；历史 GEN-034 为 `4/4`，不是当前 P0；
- query/tool 数量只作 surface inventory，不得换算为玩法完成率；
- 任何 `live` 提升必须链接 paused artifact；ACK、schema、单元测试和单场 fixture 不得冒充 OODA；
- 对已取得证据的输入直接复用，新的 live 只验证本包新增的最小事实或动作后置。

## G2-M1 目标派系最低告警

原版 `has_targeting_faction` trigger 已按 CK3 1.19.0.6 exact build 冻结：注册链最终进入
`0x283FAE0..0x283FB51` evaluator，其语义为解析完整 generation 的玩家 Character，读取
`CCharacter+0x1B8` land state，并以 `land_state+0x12C` 的非零有符号计数判断是否存在以玩家为目标的派系。

现有 `campaign-root-context-v1` 在同一双采样内发布非负 `player_targeting_faction_count`；身份、指针、计数或两次采样漂移时，
整帧以 `player_targeting_factions_unavailable` 失败。`ck3_query_turn_bundle_v1` 将它投影为
`realm.targeting_factions.{count,threatened}`、`alerts.faction_threat` 和 `realm_faction_alert_ready=true`。
该切片只关闭“是否已被派系针对”的最低告警，不宣称已经观测派系身份、类型、成员、军力、不满度、诉求或最后期限。

静态实现阶段的 MSVC Release reader/source-contract fixtures 为 GREEN，Python campaign-root、live-harness 与 turn-bundle 聚焦测试
在普通及 optimized 模式均为 `40/40`。新轮次 R639 随后在两个 paused production 场景都观测到 count `0` 并令
`realm_faction_alert_ready=true`；状态为 `production-live`。该最小告警已计入完成的 M1，但不替代后续派系深度。

## G2-M1 玩家健康观测 static-ready

`campaign-root-context-v1` 已接入 exact-build `Character.GetHealth` core `0x2619AD0`，发布 signed Q100000
`player_health`，并沿用 application-main、全 generation CharacterID 回读和双采样一致性。原生调用失败或 identity 漂移返回
`player_health_unavailable`；跨采样变化返回 `state_changed`，不把缓存、OCR 或历史值补进当前帧。

`ck3_query_turn_bundle_v1` 保留 raw health，并按原版 `death_chance_dying_health=1.5` 与 `fine_health=3.0` 形成
`dying_or_worse / below_fine / fine_or_better` 三档；`raw < 300000` 时发布 `ruler_health_below_fine`。该切片只关闭最低健康风险输入，
不宣称治疗、疾病归因、预后、生育力或死亡概率策略已经完成。

MSVC Release reader/source-contract fixtures 为 GREEN；Python campaign-root、live-harness 与 turn-bundle 聚焦测试普通及 optimized
模式均为 `42/42`。静态包本身没有启动 CK3、录制器、injector 或桌面输入；新轮次 R639 随后在既定共享双场景 gate 中观测
两个合法 health 值并令 `ruler_health_alert_ready=true`，状态为 `production-live`。没有为 health 单独安排长跑。


## G2-M1 per-held-title partition static-ready

`campaign-root-context-v1` now reads the player's exact-build held-title vector
and publishes the current first heir for every personally held county-or-higher
title. `ck3_query_turn_bundle_v1` preserves every row and derives
`single_successor / split_successors / no_primary_heir` plus a split alert.
This is the engine's current per-title result; succession law, claims,
hypothetical law changes and post-death reconciliation remain G2-M3 work.

MSVC Release reader and source-contract fixtures are GREEN. The focused
campaign-root, live-harness and turn-bundle suites pass `42/42` in normal and
optimized Python. New round R639 then observed a complete partition in both
bounded paused scenes and projected it into two ready turn bundles. Status is
`production-live`; no dedicated partition run was used.

## G2-M1 typed council observation static-ready

The exact-build campaign-root reader now enumerates the player's dynamic
active-council-task vector and publishes every materialized position with a
full-generation incumbent and owner, stable position/task keys,
general/county/court typed targets, frozen state, and
infinite/percentage/value progress. Within
`standard_landed_non_nomadic_core_v1`, the five standard positions occur
exactly once and can be proven vacant. Auxiliary vacancies remain explicitly
incomplete instead of being guessed.

The Python contract and `ck3_query_turn_bundle_v1` now preserve that component.
A fully observed supported scene can reach `available/ready=true`; a landless,
nomadic or missing-primary-title root remains available while its council is
typed unavailable. Native Release reader/serializer and source-contract
fixtures are GREEN, the bridge DLL compiles and links, and the focused Python
suite passes `47/47` in normal and optimized modes. New round R639 then
observed six occupied positions in each bounded paused scene, including all
five core positions and spouse, with matching ready turn-bundle projections.
The current-feudal slice is `production-live`.

## G2-M1 双场景 production-live 收口

首轮有界尝试在旧轮次 R638 对两个角色都返回 `direct_landed_vassals_unavailable`。该产品 RED 被完整保留；根因是新扫描器把
Character storage 中可读但低 24 位不匹配 slot 的复用/旧代际对象误判成致命失败。修复提交 `700fae3fcca5af1ebfee26d4cbaf26d3c5f0a2a9`
按照 exact-build 原版枚举器语义跳过这类旧代际对象，同时继续把不可读 pointer 和任何已接纳成员的 full-generation round-trip
失败视为 RED。原生聚焦 fixture 随补丁覆盖该非空旧代际行。

新轮次 R639 使用修复后的 fresh Release DLL `1F7DE4BCAF94959BF21E7AA110319B34D350CF8909178D9067235AD67968848E`
运行一次同进程双场景 gate。独立 ruler `29829` 与 vassal ruler `36108` 的 root、relationship vectors、partition、council 和
turn bundle 全部门为 GREEN；角色切换前后日期均为 `53178264`，PID、connection generation 与 episode 保持一致，源存档 SHA-256
仍为 `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`，cleanup 证明进程树消失。完整 artifact 位于
`Z:\ck3_mod_rewrite_process_assets\g2-m1-r639-700fae3\g2-m1-two-scene-live.json`，SHA-256
`CFF681146A344AE18FDEB36C20BDAEAFC2A30344023CC7827E9A77006C3530DB`。这关闭 M1 的既定 visible outcome，G2 为 `1/8`。
## 2026-09-14 GEN-034-D source-bound postwar evidence composer

`raiktor_three_way_exit_postwar_evidence.py` now joins the two native postwar
domains into the strict verifier input. It requires exact equality between the
retained source capture and the authorized action frame's complete persistent,
current and CArmy generation sets, and then binds the cleanup query back to the
same set. The directional persisted truce must be identical in two consecutive
reads on the successor native revision, with expiry equal to
`post_date_raw + evaluated_days * 24`. A valid `no_truce`, any surviving
generation or frame drift retains RED. ACK is never state evidence and the
composer performs no CK3, filesystem or MCP operation. The focused
recommendation/action-gate/evidence/verifier suite passes `26/26` under normal
and optimized Python. Status remains `static-ready / live=false`.

## 2026-09-14 GEN-034-D bounded action lifecycle static-ready

`run_gen034_three_way_exit_action_live_acceptance.py` now keeps the four-read
recommendation and its authorized action in one managed driver. Before any
mutation it re-snapshots the paused frame and binds the retained source capture
to the current full-generation persistent CRegiment, CArmyRegiment and CArmy
sets. A mismatch stops before submission. A continue winner executes only
`resume-map` and remains unable to close GEN-034. A termination winner executes
one authorized exit, one exact-store cleanup query, two consecutive persisted-
truce reads, one checkpoint save and one cold restore before invoking the
six-item verifier.

The default-OFF native cleanup dispatch now accepts a successful same-connection
termination ACK for its retained WarID from either `offer-white-peace-N` or
`surrender-war-N`. This fixes the real mismatch between the public white-peace
action path and the private cleanup reader. It does not enable public surrender,
change a capability ID or wire shape, or make the candidate default-on. The
focused normal/optimized suite passes `29/29` in each mode and the enabled MSVC
Release candidate DLL builds successfully. Status remains `static-ready /
live=false`; GEN-034 stays `2/4` until one bounded production lifecycle closes
C/D evidence.


## G2-M3 succession transition contract static-ready

The first M3 package freezes the existing production-live per-title first-heir
projection against the living episode ruler and one exact paused frame. A pure
post-transition comparator then admits only a paused `played_character_changed`
frame with a same-frame successor turn bundle. It reports successor identity,
matched and missing inherited predecessor titles, unexpected retention of a
title predicted elsewhere, and the successor's unrelated pre-existing titles.
The last category is informational and cannot create a false inheritance RED.

This is `static-ready / integration-live pending`. Focused tests pass `5/5` in
normal and optimized Python. It adds no native read, public MCP tool or action,
and does not yet alter the one-life terminal policy. The next package must
retain the latest valid expectation in driver state, generate the first real
reconciliation after CK3 changes the played CharacterID, and only then expose a
real-successor continuation path. Succession laws, claims and unseen holders
remain outside v1 rather than being inferred.


## G2-M3 driver-state retention fixture-ready

The native driver now persists the latest strictly validated succession
expectation as an optional additive member of its existing v2 state envelope.
Same-PID hot recovery preserves it; checkpoint/seed restore, source staging and
operator player rebind clear it and force a fresh observation. On a natural
paused `played_character_changed` frame, the driver can reconcile the retained
predecessor estate with a same-frame successor turn bundle and retain that
result for the runner.

Focused contract/driver tests pass `7/7` and three existing persistence/rebind
regressions pass `3/3`, in normal and optimized Python. This is fixture-ready;
no public MCP/native contract or planner behavior changed. The next package is
the production runner path that captures before death, performs the first
successor query/reconciliation, and continues the same campaign as that ruler.

## G2-M3 real-successor continuation static-ready

The planner service now refreshes the persisted succession expectation on each
eligible paused living frame and reconciles it on the first eligible
`played_character_changed` successor frame. After the predecessor's normal
death settlement completes, the strategy selects
`continue-as-reconciled-successor` only when both the successor identity and
predecessor-title distribution match. The driver keeps the live campaign and
process, sends no CK3 command, clears character-scoped caches, and binds a new
one-life run to CK3's already-played successor.

A missing or mismatched reconciliation blocks this path and cannot fall back to
immutable-seed replay. Focused contract/service/strategy/driver tests pass
`10/10` in normal and optimized Python, including the existing distinct seed
replay regression. Status remains `in_progress / static-ready`; one bounded
exact-build natural-death artifact is the remaining integration gate. No native
ABI, MCP tool, game file, dependency, launch configuration or load order
changed.

## G2-M3 bounded runner continuation proof static-ready

A review of the actual production owner found that `native-auto-run` still
stopped immediately after every `death-terminal`, so the previously completed
planner/driver action could not execute in an ordinary bounded campaign. The
runner now continues after a natural `played_character_changed` settlement,
verifies the matched predecessor/successor transition, unchanged PID,
connection, frame and date, zero CK3 command/restart, and the new episode
identity before gameplay resumes. Its report preserves these facts in
`natural_succession_transitions`.

Strict one-generation runs still end at death; immutable-seed next-episode runs
retain their separate restart contract. Focused normal/optimized boundary tests
pass `4/4`, including both existing terminal modes. This package changes the
private runner report shape but no native ABI, public MCP tool, DLL, game file,
dependency or load order. M3 remains `in_progress / static-ready` and global G2
remains `1/8` pending one bounded exact-build natural-death artifact.

## R676 celestial council prerequisite RED

The first production attempt at M3 expectation capture stopped on turn 1 with
`turn_bundle is unavailable`. Its only native query returned
`council_unavailable`: the campaign-root council reader admitted the existing
celestial ruler into a scope whose five-seat standard council layout does not
cover celestial ministries. The run submitted no gameplay action, advanced no
date, and cleaned the process tree successfully.

The minimal native correction adds `government_is_celestial` to the existing
out-of-scope predicate. It preserves a typed unavailable council component and
keeps all other campaign-root fields eligible to publish. Focused reader,
source-contract and mailbox fixtures pass, including a celestial case with an
invalid standard task hidden behind the scope gate. The next action is one
short corrected-DLL replay in R677; the natural-death integration gate remains
separate and receives no dedicated long run.

## R677 optional game-rule component RED and candidate contract

The three-turn R677 differential replay restored CharacterID `32904` at date
`53789952`. The celestial council correction worked far enough for the same
campaign-root query to proceed beyond council, but the root then returned
`selected_game_rule_tokens_unavailable`. The planner consequently stopped
before a turn bundle, succession expectation, gameplay command or date
advance. Managed cleanup is GREEN. Run, final driver-state and error-log
SHA-256 are `0FC0C00D7FDE01F032C17956D086B0DF076D157A424018D4327D955B2F33028D`,
`74676EC7CAC08AC8A5F8EC82852A833E5A6F1BDE0A4AA3866D2AC63804D60E08`, and
`107628E983A0A46044B5D2626B883ACFCE22BA3819EBF49E84F505917EF131AF`.

Selected game-rule enumeration is an optional campaign-root component and is
not an input to M3 succession expectation capture. The candidate contract
therefore keeps root `status=available` when this component cannot be read,
publishes `selected_game_rule_tokens=[]` and
`native_selected_game_rule_token_count=0`, sets
`selected_game_rule_tokens_ready=false` and aggregate `ready=false`, and
retains every independently observed root field. Celestial council remains a
typed unavailable component, so the derived turn bundle may be `partial`.
This preserves the distinction between an observed empty token set and a
failed token read without erasing the succession fields.

Focused native/Python validation produced candidate DLL
`68E3746D35601C3197165A91ED85C5E5AA5C362C5EEF882123487E52B2ED2B76`.
The next live gate is exactly one three-turn R678 differential replay. It must
show the partial bundle and succession expectation are usable; it must not be
reported as passed before that evidence exists. A later naturally occurring
death remains the independent M3 end-to-end transition gate, and this defect
does not authorize waiting for or manufacturing one during R678.

## R678 executor timeout RED and mailbox partial-admission gap

R678 ran the three-turn candidate from commit `764e1c4` with DLL
`68E3746D35601C3197165A91ED85C5E5AA5C362C5EEF882123487E52B2ED2B76`.
Preflight was GREEN, but command-history entry `621` ended as
`timeout_cancelled_before_execution`: the application-main executor never took
the campaign-root request. The attempt therefore completed `0/1` turns, sent
no gameplay input, retained date `53789952`, captured no succession
expectation, and produced no campaign-root payload from which to judge the
optional rule-token contract. Cleanup is GREEN and the old round R678 process
is terminated. Metadata, run-log, final driver-state and cleanup-inventory
SHA-256 are `DF7401C0B447B6312843A6AB670FBFFAA37AC6C2EC152BB2C51E8606DD7016BD`,
`51D66A8DBC032B858B9C62351FF4FE30993CA2A6FE5863B2A65103B1111456BF`,
`2CE3FA573E6A52AB586AD8E743FC3AFF09EBB9F902C0E3202C4DAA78FDE79BFD`, and
`D7007C3D0D496550463BDE6112DE3ED869D367DACB7DB8BE9F384BC61B0FA303`.

A separate post-run source inspection found a deterministic downstream gap;
it is not presented as the cause of this request-not-executed timeout.
`campaign_root_context_v1_mailbox.cpp` currently recognizes
`typed_available` only when aggregate `readiness.ready=true`. The candidate's
intended optional-component result is deliberately `status=available` with
`selected_game_rule_tokens_ready=false` and `ready=false`, so a future
successfully executed partial read would be converted to `internal_error` at
mailbox completion. The next package must align that mailbox predicate and its
focused fixture with the partial-ready root contract. Only after that repair
may one short new round R679 replay test root publication, partial turn-bundle
construction and succession-expectation capture. R678 remains RED, the
optional-component contract is not production-live, and the independent
natural-death M3 gate remains pending.

## R680 cold-pump RED, FIX3 and R681 bounded GREEN

R680 ran FIX2 commit `324dab573f48b9ab3439a9a0eb0eb1c8edb2478f`
once under the three-turn ceiling. Its first campaign-root ticket still ended
`timeout_cancelled_before_execution`: pump epoch stayed `9849 -> 9849`,
executor starts stayed `0 -> 0`, and executed requests stayed `0 -> 0`. The
attempt completed `0/1` turns without gameplay or date advance. Probe, run,
driver and cleanup-inventory SHA-256 are
`A1E9B898DC5015EE84A64EE57C7DB05CA7B3A6172CE88C64A537424BF082B997`,
`4C34D4FFD31B18455B640B8B78E956ACF1919CD126AD47FE9E91277C48DC18DD`,
`FCDB79A80C9A0B431DD5F9C4D986CDE61781770650CF697BBABF2832777619EE`,
and `F27BCDE1C86F37E60CC900E308CD504352E58A7D1627DB35D156D05827F0611F`.

FIX3 commit `080bc507ee9c2e1c2fa1decd787a3927c15a12e4` requires native
auto-run to observe a pump epoch newer than the current cold binding baseline
before it declares readiness. Focused normal and Python `-O` tests pass `2/2`
in each mode. R681 subsequently completed the typed campaign-root request,
which proves behaviorally that the fresh-epoch gate passed and the executor
started and executed. The successful exact epoch values were not serialized
and are not part of the evidence claim.

R681 completed all `3/3` bounded turns. Campaign root was `available`;
celestial council was typed `unavailable` with
`outside_standard_landed_non_nomadic_core_scope`; selected game-rule tokens
were `[]` with native count `0`, component readiness false and aggregate
readiness false. The planner consumed the resulting `partial` turn bundle and
captured successor expectation `32904 -> 88187` for primary county title
`16761`. Two queries and one `life-advance` advanced the date 30 days from
`53789952` to `53790672`. Final checkpoint SHA-256 is
`CDCC3771B1179667ECD017817781B2A93A412EA82EC9455B08EECE170F2FBC61`
at history index `625`.

The frozen artifact is
`Z:\ck3_mod_rewrite_process_assets\g2-m3-r681-cold-pump-edge-080bc50`.
Acceptance, run, final driver-state and cleanup-inventory SHA-256 are
`2BED139B270AB09C18582AAF67E418E17B012C017A70C0A18BF0830259246B14`,
`EFBFF36A2C21EB4809396BD1A8FF1899023175C23C52F228CB4CB53403A4C866`,
`19421B49B2C474C443B1E594759EAA7546411F85209394D51618C7F195F40734`,
and `086138C344901BFF61A571A7ED96100DBB1E441CB06067BF85FCD9EC0636B2D1`.
Cleanup is GREEN and CK3/injector are zero.

This closes the mailbox/cold-readiness operational blocker. G2-M3 remains
`in_progress` and global G2 remains `1/8`. Its only integration gate is one
bounded naturally encountered exact-build death that reconciles actual
successor/title distribution against the captured expectation and continues
in the same campaign as the real successor; no dedicated death long run is
authorized.

## R692 council candidate capability RED

Current round R692 executed the sealed `g2-m4-council16-r692-9cdb430`
candidate once against exact CK3 `1.19.0.6`. The private council probe prepared
and published one result, but it was typed `unavailable` with
`application_main_thread_required`: `last_submit_result=0`,
`last_wait_result=4`, and `executor_started_requests=0`. The expected steward
candidate vector was therefore never collected, no candidate-completeness or
temporary-vector-release assertion passed, and the result is a **capability
RED** rather than evidence of a usable council observation.

The attempt remained paused and read-only: it submitted no gameplay command,
performed no UI input or date advance, and left both source and target save
SHA-256 unchanged at
`9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`.
Cleanup proved the CK3 process tree and watchdog gone with final inventory
zero. Current round R692 is terminated. The immutable evidence manifest is
`Z:\ck3_mod_rewrite_process_assets\g2-m4-council16-r692-9cdb430\live-r692\postrun-evidence-manifest.json`,
SHA-256
`589FFE1526F3C98DFC5C04E5F0C8A48EC41D6DB893CC5497AE459781D4F2FFCB`.

`seal_r692_red.py` was a one-time helper with `reason=现场封存`; its only effect
was writing the post-run manifest and checksum. Its impact is limited to the
immutable evidence inventory, its reuse plan is no productization, and its
migration deadline is this work-package close, when the manifest replaces the
script as the durable record.

No formal planner/strategy path consumed this private result. G2-M4 therefore
remains `in_progress`, its council adjustment/action/postcondition loop remains
open, and global G2 remains `1/8`. This corrects the prose-table drift from
`not started` to the machine-readable `g2-requirements-v1` state without
changing the fixed denominator or claiming a new completed milestone.

## R693 private steward-candidate reader production-live primitive

New round R693 executed sealed candidate `g2-m4-council18-r693-5e0c5d5` once
against exact CK3 `1.19.0.6` from source commit
`41bd2d5d0c159676876f21adc3845cf0afeeaf97`. The application-main mailbox
started and executed one request. The private reader returned `available` for
owner `29829`, published a complete 11-character steward-candidate vector,
released the temporary native vector and persisted no raw pointer fields. This
closes the R692 private-reader capability RED.

The run remained paused and read-only with zero UI/gameplay actions, no date
advance and no save mutation. Both save hashes stayed
`9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`;
managed cleanup proved the CK3 process tree and watchdog absent. The immutable
post-run manifest SHA-256 is
`FC59D8D8F001B6B6F6A5ACD041EFBA78596F7D837A54819A8B3F3A2E3EAFABC4`.

This evidence is a `production-live primitive`. It did not pass through the
formal planner, did not submit a Council assignment and did not verify a
postcondition or next-cycle policy response. G2-M4 therefore remains
`in_progress`: public/formal candidate semantics, legal assignment,
independent postcondition and subsequent policy consumption remain open, as do
construction and a real vassal/faction intervention. Global G2 stays `1/8`.
