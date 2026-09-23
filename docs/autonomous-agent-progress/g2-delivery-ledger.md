# G2 交付门增量台账（更新至 2026-09-22 Asia/Shanghai）

权威 g2-requirements-v1.json 当前为 2/8，G2-M0 与 G2-M1 complete。可运行预览是额外交付切片；受控查询、静态实现和有界战术均不自动完成正式里程碑。CK3 按持久单实例 R{n} 台账追溯，RED、未执行和证据不足分开记账。

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标准封建有界预览 | GO，用户可获取、启动和冷恢复；仅冻结组合与已验范围 | native-auto-run / ck3_auto_turn | [冻结 ZIP](Z:/ck3_mod_rewrite_process_assets/g2-preview-bundle-d11268f1-eefc88e4/g2-preview-candidate-d11268f1-eefc88e4.zip) SHA 0E233DCB...4EB2；外部 GO 清单 SHA C4AF9C...395E；Python d11268f/native eefc88e；[操作文档](../ck3-native-ai/g2-preview-release.md) | R701 20/20 自然 pay_ransom 唯一 typed reject，独立 pending 清空、下一正式 turn 消费；R706 从 ZIP 真正解压后正式 5/5，不虚称新增语义动作 | R702 stop-file 边界 checkpoint/回收；R703 公共 feudal eligibility；R704 与 R706 真正新进程同 episode/目标冷恢复 | 冻结范围外状态停止并保留 RED；整局主链另列，/root | stop 补丁与文档最终 144956e 在 master；临时远端/集成引用已清；旧独立 clone 物理清理被自动审批阻塞 |
| 议会四类 final gate 与正式消费 | 未完成，公共 query/action 未注册未广告 | 受控私有 gate；正式入口尚未接通 | 既有 glue/native master c31886f；分类器原 3aaffde→master f4bdef3；三类自然正例 exact 场景合同原 e110862→master 2577abb，清单 SHA 4844DC...AF92B | R695/R696 already-councillor 合法拒绝与替换；R700 新进程独立 incumbent 33433；R695/R700 原生候选各 11/11 全部 candidate_is_guest=false，guest-positive、候选 pending-positive、fireability-denial 尚缺；typed receipt 后正式下一 turn 未证 | R700 gate-only 冷查询，不是正式目标恢复 | guest 需未招募/非法任命 native 行；candidate pending 需玩家→该候选的真实待回复提案、原生 recipient 同人；fireability denial 需 naturally force_onto_council 原版锁且 incumbent_can_be_fired=false；四门后再接公共查询→策略→typed 任命→独立 incumbent→下一 turn；/root | 分类器与 2577abb 场景合同均等价 rebase/master FF，原/集成远端/local 临时 refs、worktree/跟踪引用即时清；既有 clean clone 物理清理阻塞 |
| GEN-034 战争 C/D | R729 正式新军队物质行军与下一 turn 消费 GREEN；R728 六轮仅前决策、证据不足；R724 只读拒绝 RED 留档且 retry-live 未触发；终局/休战 C、特殊 D 仍未完成 | native-auto-run；同帧 continue/white peace/surrender 正式三择一，终局只能唯一提交 | Python 1f117ab→master；native f342232→master，R729 DLL SHA 267860BF...B2017；R729 [候选清单](Z:/ck3_mod_rewrite_process_assets/g2-gen034-c-r727-continuity12-20260916/manifest.json) SHA D874BEAD...14ED；public 终局未广告 | R727 冷续 12/12、28 游戏日，旧 Army50331653 省5613→5615→5616 后下 turn 消费；R728 冷续 6/6、171.576 秒，全部查询/预览、0 typed/日期推进，CLI1 run_bound_exhausted=证据不足而非 RED；R729 从原 R727 pair 冷续 12/12/CLI0/175.668 秒、8 游戏日，正式 typed Army50331957→8755 唯一 history#160，独立 paused 省2629→2630、目标仍8755，t9 正式终局 options 读 available，WarID33554473/score-42，终局动作0；R724 read RED 未复现、重试分支未执行 | R729 新进程 PID33664 创建00:31:21 已回收；同 actor29829/episode/WarID 配对 checkpoint date53193432/index168，save SHA 4A7AAEF8...20E、driver SHA F07470D3...EC0；旧 move5604/8755 各一次，新 move8755 一次，无盲重发 | C 仍缺同决策帧合法终局的唯一正式动作、物质 war disappearance/truce 与冷恢复；D 仍缺合法 Robert 普通场景源兵/战后损失；Army50331653 消失原因 unknown/B1 watch，若阻决策补最小只读口；/root 单实例 | 战争 f342、Python 1f117ab 已 FF master 且临时 refs/worktree 清；原独立 clean clone 物理删除自动审批阻塞 |
| 自然事件与同战役自然继承 | 指定事件与自然继承待实机；不把两种死亡混为一门 | 普通 production 正式策略 | .1104 exact 调用链原 a6535a4→master eb5bc32；.1007/继承 exact 合同 master 64808628；自然 paused 锚点清单 SHA 3AF2344A...08CF | R708 自然 chancellor_task.1104 合法 typed 单选，独立下一 paused 窗口清空、R709 不重复；+30 好感物质结果未观测。.1007 是活着的玩家继承人自然死亡事件，与玩家本人自然死亡接续不同；.0030 exact 原版依赖 TGP celestial government，标准封建整局不能冒充它；R710/R721 正式健康 raw418462/scale100000、首继承人38822与分封预期保留，R721 paused active_event=null/玩家仍活；继承人健康 unknown，既有事件/继承反应观测口可用，但无自然 `.1007` 或玩家死亡近点 | R709 事件后同战役新进程续行；.1007 stress 后置/配对 cold 与同 campaign 自然继承仍缺 | 在合适 bounded/阶段运行分别取自然 .1007、自然 played death→继承人、另设合法 celestial .0030 场景；自然事件/继承包与 /root | 两份 exact 文档均 master FF 且临时分支/worktree 清 |
| 和平建设/生活方式/封臣派系 | R726 世界定义 `definition_identity` 真实 RED；final4fc 仅私有失败索引/阶段诊断候选 READY、未复验；公开建设 OFF | default-OFF 受控 player-world 定义/原生最终合法性只读；正式建设待合法动作后置 | world 原 a819a85→master39e25cd、freezer f3defbb→master3c7beba、诊断原 b21c08a→master4fc2b9f；[R726诊断候选](Z:/ck3_mod_rewrite_process_assets/g2m4-defidentity-diag-master4fc2-20260916/candidate-manifest.json) SHA29858DCB...9ED4D7，Release DLL SHA E96A4FD5...3E5F12 | R722 六个真实直辖 barony Title→Province；R726 同 paused actor29829/rev3/date53178312、slot42 executor1/六行，但 definition count=null、failure=definition_identity/CLI1/178.068 秒，0动作/日期/UI；诊断版未给 building legality/cost/action | R726 源 pair saveSHA D8BDC3...0147 byte unchanged，CK3 PID83700/job/watchdog 回收；新短复验仅同源只读，不冒充建设 checkpoint | /root 下一单实例聚焦 R726 同源短复验，读取首失败 index/stage/vtable RVA/TypeID 后修最小原版口；真实建设、生活方式、封臣/派系与两年闭环仍缺，广告OFF | 三包+诊断 final4fc 均 master FF/临时 refs/worktree 清；旧 clean clone 物理清理自动审批阻塞 |
| 家庭外交与 M6/M7 最小连续面 | R725 只读源 GREEN 但旧 native final-answer raw0 被误判不合法（B1）；finalab 修正已 master/聚焦通过，最终同版 private live 待执行；五合法联合评分/typed 婚姻仍缺 | default-OFF 私有 CanSend/AI acceptance 只读；公共 marriage/ad OFF | observed-heir 原 b282e4b→master539c94f；answer raw0 原2404647→masterab7899c，stock AL=0 接受、1 接受、2 拒绝、>=3 不可用，Debug/Release与正常/-O焦点 GREEN；新同版制品构建中 | R725 同 paused actor29829/heir38822、公战候选30行、私有 family CanSend 657 distinct 行且AI acceptance positive，answer raw0 657/657；旧适配不能将其称为0或657合法；0动作/UI/日期；finalab 的真实合法数待复验 | R725 源/目标 saveSHA9104CC...CC63 byte unchanged、CK3 PID回收；新正式婚姻目标 cold 未证 | M5 finalab 私有真实复验后需至少五不同合法候选联合机会成本选择、typed 婚姻、独立结果/目标冷恢复；不凑非法候选；/root与m5_legal_scene | finalab 已 FF master、远端/local 临时 refs/worktree 清；旧 clean clone 物理清理自动审批阻塞 |
| 首条独立 1066→1166 前缀及整局 | FEUDAL selected-model 私有 guarded read-only source final8ea 已 master；selected paused 身份/typed StartGame/独立1066配对种子未获实机；百年/整局/双种子未执行 | 当前正式 native-auto-run 仅接受 paired checkpoint；新局 selector/StartGame public OFF | selected-model producer 原4bd85e17→master0ecd1692、private wire 原f32fe858→master4223a5cc、组哨兵 B0 原0923b933→master8ea06348；/Od,/O2/Release聚焦 GREEN，final8ea 版本候选待封 | R719 正式 NewGame+Bookmarks 只读根树可用，未见当前 selected Bookmark/角色政府日期；exact source：ClearGroup 可能写非 key sentinel，group key仅诊断，选中 Bookmark 身份/角色边界/封建政体/1066日期仍硬门。StartGame 回调仅写 pending，GUI约1.45秒 OnStart 才启动；ACK不能证明开局，禁止双调 OnStart | R719 进程回收；尚无新独立1066 paused feudal map或首次 paired save/driver，历史 fixture 不得替代 | /root 单实例先 final8ea 私有 paused selected-model 只读，再合法 typed 选择/StartGame、独立 paused 地图+首 checkpoint；之后冻结第一种子 1066→1166 前缀并继续整局，第二种子仍独立；feudal_start_game | final4223 与 final8ea 均 master FF；final8ea 原 tip0923 CAS远端删除、root集成worktree/ref清、clone切clean master且工作/tracking ref清；旧独立 clone 物理清理自动审批阻塞 |


R719 Bookmarks 只读 GREEN 仍未创建首种子；R720 M5 exact `ranked_source_unavailable/strategy_unavailable` RED 保留、正式婚姻候选数未知。R721 从 R710 配对点 8/8、唯一新 typed move8755 后续路线消费与物理 checkpoint；R722 M4 私有 player-model 六条 barony 来源真实而 UI 关闭定义0，CLI2 证据不足、公共能力 OFF；R723 新进程从 R721 配对点 4/4、同目标/WarID/actor、历史前缀一致且无重复旧 move、新 paired checkpoint。R723 原先把未到首跳的静止军队初判物质 RED，保留现场并依据 exact route query ETA53192568（当前53192424）更正为到 ETA 前证据不足，不报物质 GREEN；围城强度0语义继续 exact 原版调查，停止不变 1 日 horizon 重试，优先一次跨 ETA 有界正式观察。Council guest 原生候选 R695/R700 全 false，新 guest-positive 场景未冻结，议会仍 OFF。自然 `.1007`/同战役自然死亡无近点；健康/继承预期已有生产口，不猜继承人健康。当前单实例库存0、最新 R723 已回收，团队 13 slots 含 /root，W=12、A=6（FEUDAL selected-model、独立 GUI ABI trace、M4 world definitions、M5 played-heir family query、War 三择一策略、War ETA/围城原版调查），无其他真正 READY 非冲突包；CK3 下一候选正从 R723 配对点冻结跨 ETA 断言，代码包仍聚焦编译/源查。所有本轮新制品与进程版本逐轮分开；预览 d112/eefc 与 open_kaishek main64cd 的已验兼容未变。GEN-034 2/4，G2 权威1/8，100 年、1066→1453、第二独立种子未执行。已集成独立 clean clone 物理删除和 FEUDAL 旧 sparse lock 删除被自动审批 blocked by policy，均有负责人、保留现场，不妨碍安全隔离新工作。

R724 跨 ETA 已有真实 army 5604→5615，到达日后 turn15 campaign-root 只读拒绝 RED；修复 60144b8/1f117ab 仅 Python 合同正常/-O 6/6，聚焦候选 R727 READY_NO_LAUNCH，待 R726 回收。R725 标准封建玩家/首继承人私有 CanSend 657/657 但旧 final-answer raw0 映射待 exact 改动与新实机；婚姻动作无证。R726 M4 world 定义/原版最终合法只读候选当前唯一实例 PID83700，结果待核。首种子 FEUDAL model source 静态 master0ecd，但 selected paused 身份/新独立 paired save 未见。预览冻结 ZIP GO 范围不变，GEN-034 2/4，权威 G2 1/8，100年/首整局/第二种子未执行。团队13含协调者，活跃独立实现 FEUDAL/M5/M4/Council/War 冻结及协调者；CK3 唯一 owner /root，轮次R726。已合入临时远端/本地 refs和 worktree 清，clean 独立 clone 物理递归删除遭自动审批 blocked by policy，标清理阻塞、继续使用隔离源，不影响当前运行。

R726 M4定义身份 private RED/CLI1，same paused 六块直辖地、private executor1而world definition_identity/count null/native合法未测；CK3回收、源pair不变，M4包聚焦 exact 修。R727正式 War 冷恢复已从安全配对date53192568在新唯一 CK3 PID174812运行，12turn/900s，结果待核。不因另链M4 RED停止已就绪战争；预览 GO 范围不变，GEN0342/4、G2权威1/8，首1066/百年/完整/双种子未执行。

R727官方从R724安全配对点12/12/196.704s，军队5613→5615→5616并由下一正式turn消费，旧typed move一次且没有终局；新物理配对checkpoint date53193240/index151有效，CK3回收。原campaign-root拒绝在此版本未复现，retry-live分支没有触发；turn11 ArmyID真实消失，下一正式turn转原生战争终局查询，无B0卡死证据、原因unknown/B1 watch。War下个4–6turn冷候选准备中；M4 R726 definition_identity RED聚焦新私有诊断，FEUDAL/M5单job编译/协议广告OFF。预览GO、GEN0342/4、权威G21/8，1066首独立种子/百年/整局/双种子未验。

R729 当前 CK3 存活实例 0，下一实机就绪队列含 FEUDAL final8ea selected-model（候选重冻中）、M4 final4fc private 失败阶段短复验（READY）与 M5 finalab raw0 只读复验（Release 重编中）；仅 /root 可操作单实例。团队容量 13 含协调者，W=12；当前有效独立 worker FEUDAL/M4/M5 三包，/root 负责报告、master 集成和实机。用户预览 GO、GEN-034 2/4、权威 G2 1/8 不变。open_kaishek main64cd4e0 与冻结预览 d112/eefc 已验；FEUDAL/M5 仍 private/ad OFF、无下游消费者，公开启用前先锁 typed 契约和被动适配。

## 2026-09-17 R797-R802 current delivery override

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标准封建有界预览 | GO，用户可获取；广告范围仍是冻结 R783 slice | 包内 `g2_preview_operator.py` / `native-auto-run` | ZIP `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r783-stage-20260916T134805Z-6cfba744\g2-preview-ordinary-5ac64152-r783.zip`，SHA `AA9CABB5...517C`；GO 清单 `A5CB85FE...4B1D` | R790-R792 资格证据不变；R800-R802 尚未进入 ZIP，不能扩大广告 | 包内 stop/checkpoint 与 R792 新进程恢复已验 | 新包需单独按现有 bounded contract 构建/合格化；/root | 冻结包无临时分支依赖 |
| Council 四类 final gate | 1/4；R797 新场景仍无后三类正例，公共 OFF | 私有 gate-only query | R797 report `B6345292...4641` | 14 provider/11 ordinary；already3、guest0、pending0、replacement-denial0；gameplay/date/checkpoint0 | query-only cleanup GREEN，不是正式目标恢复 | 等 materially-different guest/pending/non-fireable scene；不重复 h260；/root | Council materializer `0aa366ef` 已 FF master；临时 refs 已清 |
| Ordinary WarID5 terminal loop | **production-live loop for observed branch** | 正式 `native-auto-run`; recovery query `game.command.query-outbound-war-white-peace-status-v1-N` | commits `b9b6f249`/`881e1ba5`/`f5a8914d`/`36a25a55`/`c9c371b4`/`851c36dc`/`aba36a4e`; R801 report `E6E47677...48C6` | 同帧三择一→唯一 white peace→即时 pending checkpoint→独立 WarID5 消失→下一 turn 解散残军→和平 checkpoint | R802 新进程恢复 h289，零 reoffer/declare，正式推进32天并保存 h293 `DFC96CFD...71AF7` / `7C79FE4C...48EF0` | ordinary B0 已关；Raiktor GEN-034 C/D、自然继承、治理和整局仍开；/root | 所有代码均 ordinary FF 到 master，远端/local 临时分支即时删除 |
| G2 权威状态 | **1/8**，仅 M1 complete | `g2-requirements-v1.json` | 定义与分母未变 | ordinary war closure 不自动完成任何正式 milestone | 无新增 milestone restore claim | 首整局、第二种子及余下矩阵继续；/root | 不适用 |

## 2026-09-22 current delivery override

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标准封建有界预览 | **GO，用户可获取、启动、停止和冷恢复**；范围仍为冻结 R888 slice | 包内 `g2_preview_operator.py` / `native_auto_run` | ZIP `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r888-d559faa6-stage-20260921\g2-preview-ordinary-d559faa6-r888.zip`, SHA `F7FAC0F5...18E9F6`; qualification SHA `0A74F822...E2757` | R0019 正式非空动作、独立后置与下一 turn 消费；R0020/R0022 新进程继续同一目标；R0021 受控停止 | final pair h1484 checkpoint `7121CCE3...386F`, driver `E9B7730E...4674` | 任意用户存档、自然事件/继承、Council 与整局仍未广告；`/root` | 冻结包不依赖临时 Git 分支 |
| GEN-034 / G2-M0 | **complete；4/4** | formal `native_auto_run` same-session terminal callback | agent `8ec1153e`; R0043 outer `9294D8B8...13EE`, native `2B726601...2D6` | 同帧三择一，唯一 `surrender-war-16777285`；独立验证 WarID、资源、方向性 truce、24 regiments；下一正式 turn 消费且零重放 | checkpoint `A89BCF26...B296`; PID `77580→41264` 真冷恢复；cleanup GREEN | M0 无剩余 blocker；后续推进 M2/M3/M4 和整局 | implementation branch 已删；runtime worktree仅作为冻结证据依赖保留 |
| 普通 production continuation | **R0044 B0 closed；R0045/R0046 GREEN** | current-master `g2_preview_operator.py run` / `native_auto_run` | fix master `0636a81f`; R0044 `EDE952DC...2B08`; R0045 `00296B7E...E877`; R0046 `E1513900...D684` | R0045 formal rally query→两次一日推进→下一 turn 消费；R0046 100/100、+28d、contact→battle epoch→旧军消失→raise 新军→继续 | R0045 从 h1511 新进程恢复；R0046 再从 h1536 新进程恢复；当前 h1662 pair `03D08AE8...B301` / `13BFB01D...A842`，cleanup/process-zero GREEN | 自然 `.0030`/`.1007`、玩家死亡、Council 三缺门、100年与整局仍开；`/root` | fix 原 `72a88f29`→`0636a81f`；临时远端/local 分支已删，current detached runtime仅服务下一续跑 |
| G2 权威状态 | **2/8**，M0/M1 complete | `g2-requirements-v1.json` | 固定定义与分母未变 | R0043 完整闭合 M0 visible outcome | M0 recovery chain complete | M2/M3/M4、首整局、第二种子及余下矩阵继续；`/root` | 不适用 |

## 2026-09-22 当轮增量更正（覆盖上表的旧预览 GO）

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 用户可独立启动的预览 | **NO-GO**：旧 R888 ZIP 缺包内 run-ID 分配器；PRV-001 新 ZIP 仅静态自包含，尚未实机资格化 | 包内 `g2_preview_operator.py` / `native_auto_run`，公开命令以精确新包验收为准 | 新候选 `Z:\ck3_mod_rewrite\.task-tmp\PRV-001\candidate-b7be2a4\g2-preview-ordinary-b7be2a4-prv001.zip`，SHA `FDE7BE61...45EED3`，2,361 条目；agent b7be2a4，native 434f832d | R888 旧语义动作/下一 turn 证据可复用作对照，但不能给新 ZIP 盖 GO | 新包 no-launch Z 盘状态 GREEN；还缺 fresh-extraction eligibility、正式动作与后帧、stop/checkpoint、新 PID cold restore | PRV-002 准备精确提取与 manifest；唯一 CK3 owner RUN-001 实机验收；R0050 战争 B0 必须受影响短复验 | 新候选无临时 Git 分支，仍不能作为交付包 |
| Council 四门 | `1/4`；action/query 公共注册与广告 OFF | 私有 query-only 受控 gate | 零填充 R0050/R0051 场景修复原 `441456d`→master `8b6202f`，normal/`-O` 各 11/11 | R0047 already-councillor 已验，guest/pending/replacement-fireability 缺正例；R0051 差异场景待执行 | h1809 成对源快照有效；不等于正式恢复 | RUN-001 唯一 CK3 owner 使用 Z 显式 run-ID root、CNL 场景 action OFF；门全闭后再接正式消费 | CNL 原远端分支 CAS 删除，clean Z worktree/local ref/tracking 清理已核 |
| Ordinary production / WAR-B0-R0050 | R0049 100/100 GREEN；R0050 turn32 RED 保留 | `native_auto_run` | R0049 report `9377808A...FF03B`；R0050 report `3D2688A5...59421`；策略修复待 WAR-B0-R0050 | R0049 43 gameplay/16 visible 到 h1782；R0050 31 成功 turn、12 gameplay，score=-100 防守方当前 rally 安全输入被旧筛选漏掉；未投降或盲重复 | R0050 h1809/date53284392 save `93DB4D03...5A770D` / driver `1FA45B1E...70CAB9`，CK3 回收 | WAR-B0-R0050 先冻结 exact 原生树，后做最小 score 边界修复及受影响聚焦实机；surrender terms unknown 不可代选 | 隔离 Z worktree/分支进行中 |
| 治理建设与 M5 输入 | GOV-CONS-01 和 M5-INPUT-01 开发中，公共广告 OFF | 既有 private construction transport；正式 pending 消费尚未发布 | GOV-FAM-001 仅隔离 Python 消费、normal/`-O`，尚未 commit；M5 只读核对 | R753/756 建设 private 动作、独立后帧和冷恢复已有；不能冒充正式策略消费或两年闭环 | 待新正式合同实机 | GOV-FAM-001、CNL-001（M5 只读）；生活方式/真实封臣/五合法候选仍缺 | 工作分支未集成，不清理 |
| G2 权威状态 | **2/8**，M0/M1 complete | `g2-requirements-v1.json` | 当前 master `8b6202f` 不更改八项定义/分母 | R0049/50 不新增完整 milestone | 无新增 milestone recovery claim | M2/M3/M4、百年、首整局、独立第二种子继续 | 不适用 |

本轮任务临时根为 `Z:\ck3_mod_rewrite\.task-tmp`；四文件 run-ID 账本已逐哈希迁到 `Z:\ck3_mod_rewrite_process_assets\g2-live-run-ids-v1`，只以该根作为本轮活动写入根。旧 C 命名空间及三个含历史运行证据的 C 临时目录尚未删除；前者删除被工具政策拒绝，后者须先无凭据迁移并核验，不称清理完成。集成负责人承认本次 master 推送返回必需检查绕过提示；后续禁止直接推受保护 master，改走满足检查且 rebase-only 的 PR 路径。

R0051 实机增量：上述 Council 四门仍 `1/4`，不是新的动作或消费证据。受控私有只读报告 `Z:\ck3_mod_rewrite\.task-tmp\RUN-001\council-h1809-candidate\live-R0051\report.json` SHA-256 `D725CBE1AF1493631FB2B1D7D0137A1E947028953E9897C86D610D36EFDF9FBD`，201.616 秒、0 动作/日期/存档变化、CK3 PID117464 回收；isolated counts `already=1/guest=0/candidate_pending=0/replacement_denial=0`。同一 h1809 场景退役，CNL-DISTINCT-01 只读寻找真实不同场景；唯一 CK3 owner RUN-001 待 PRV-002 no-launch 准备后消费新 ZIP 实机门。Z 账本 seq51 completed-green，下一轮 R0052；三处旧 C 临时目录非凭据证据 6,151 文件 / 1,153,921,845 B 已逐 SHA256 迁到 Z，源和账号文件保留。后续代码仅在 [PR #2](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/2) 受保护检查 GREEN 后 rebase 集成，CLA/signatures 已过，static pending。

## 2026-09-22 预览门最新覆盖（R0052–R0056）

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 用户自包含普通封建预览 | **NO-GO**；R888 缺包内分配器，PRV-001 无非空动作，PRV-003 60-turn 内确定性战争 RED | 从 ZIP 新解压 `g2_preview_operator.py` → `native_auto_run` | PRV-003 agent `b7be2a4`/native `434f832d` ZIP SHA `0E6B2B0E...D29AC5`；最终 master `fadc2e5` 含 WAR 修复，PRV-004 重封待验 | R0052 新解压 eligibility GREEN；R0053 40/40 但 0 typed；R0055 新解压 eligibility GREEN；R0056 turn47 typed 征兵，独立 army `[]→[301989888]`，turn48/49 正式消费；turn58/date53284488 `native_war_no_safe_target` RED，报告 SHA `6D5B175D...6915667`。turn52 forced single displayed event option 的 instance 已于独立后帧清空、turn53 消费，但语义效果未知，不能充当自然事件质量门 | R0056 h1737 安全 pair 保留、进程回收；整包 stop/checkpoint/新 PID cold restore **尚未执行** | `/root/preview_delivery` 重封最终 master+原始 h1662 pair；`/root/runtime_preflight` 唯一 CK3 owner 做同一 ZIP 的 60-turn＋stop＋cold；不能缩短合同掩盖 turn58 RED | PR #2 已通过受保护 rebase 合入 `fadc2e5`，对应临时分支/worktree 已即时清；PRV 制品不依赖该 worktree |
| WAR score=-100 B0 | 开发源短复验 GREEN；最终主线/预览同版待验 | 正式策略同帧安全静止首府查询，证明性推进 | WAR 原 `4152086`→master `6e6fb4b`，PR #2 必需检查 GREEN | R0054 从 h1809 20/20；score=-100 的四敌军 same-frame horizon，证明性一日推进、下一 turn 消费，无终局副作用；报告 SHA `CAE4D413...F3F0D2C5`，不是最终 master 运行 | R0054 CK3 回收、paired checkpoint；PRV-004 需新状态和新进程正式冷恢复 | R0056 的旧 ZIP 再次暴露同类 B0；新 ZIP 同版同窗口受影响验收，owner `/root/runtime_preflight` | 最终 master 已集成，临时分支清理核验 |
| Council / G2 | Council `1/4`、公共 OFF；权威 G2 `2/8`（M0/M1） | Council 私有 query-only；G2 JSON 不改 | master `fadc2e5` | R0051 仅 already-councillor 正例，其余三门无真实正例；R0056 战争/征兵不完成新里程碑 | 普通预览 cold 未过 | 继续寻找 materially distinct 自然场景；整局/双种子未完成 | 无待清理的已集成临时分支 |

本轮任务临时根 `Z:\ck3_mod_rewrite\.task-tmp`，活动 run-ID 根 `Z:\ck3_mod_rewrite_process_assets\g2-live-run-ids-v1`。用户当前不能独立取得已验合格包；已通过的单动作子门不能抵消整包 RED。旧 C 文件虽已迁移核验，物理旧目录删除仍被工具政策拒绝，不能报清理完成。

R0057–R0059 精确 PRV-004 增量（覆盖上表 PRV-004 待验）：最终 master `fadc2e5`/native `434f832d`、原 h1662 pair 的新自包含 ZIP SHA `BBCF366E530E668CC2D0AD09BDB720BDF23AF45AD674C6543ED2F9214CFC74DA`；fresh 2367/2367 文件与 no-launch GREEN。R0057 read-only eligibility GREEN 报告 SHA `491F0C55...11653A4`。R0058 正式 60/60、exit0、报告 SHA `D072EB21...D6165B0`：turn47 唯一 typed 征兵、独立 ArmyID301989888 和 turn48/49 消费；旧 turn58 RED 位置转为同帧四敌军 horizon 查询，turn60 无阻塞、paired checkpoint、进程回收。R0059 从该 checkpoint 新进程正式继续，turn11 解散残军、turn12 新 h1761 成对 checkpoint（save `FC938E20...57599`/driver `B39B9555...F6551`），但在 turn18/date53285904 的真实 `grant_vassal_interaction` pending 因定义未分类而 `blocked`/exit1，报告 SHA `F4C0D427...E0DF54`；**尚未发出停止请求**，不能称 stop/cold 合格。旧 pending ID1744830474、AI sender32718、玩家 recipient31853、secondary_actor31506，native reject 同帧合法且 typed 可达，未提交任何回复、checkpoint 未污染。CK3=0，PRV-004 整包仍 **NO-GO**；PEND-B0-R0059 先落 exact-build 原生互动树，再做只拒绝的最小正式策略与受影响聚焦恢复，绝不能通过普通 allowlist 的 unique-accept 路径意外转封臣。权威 G2 `2/8`、Council `1/4` 不变。

## 2026-09-22 当前覆盖：PRV-005 R0061–R0065

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 自包含普通封建预览 | **NO-GO**；动作/停止窄门已验，冷恢复连续性因真实事件 RED 未过 | 精确 ZIP 包内 `g2_preview_operator.py` → `native_auto_run` | [PRV-005 ZIP](Z:/ck3_mod_rewrite/.task-tmp/PRV-005/candidate-h1662-3da54dc/g2-preview-ordinary-h1662-3da54dc-prv005.zip) SHA `F5EB76578A9B3E4D9839BB8F7A9135FB41A7C298D4601EAC10B5BE739AB282CD`；agent master `3da54dc`、native `434f832d`，原 h1662，2370 ZIP entries/2369 SHA GREEN | R0061 fresh ZIP read-only GREEN；R0062 60/60 turn47 typed raise、独立 ArmyID352321560、turn48/49 consume，报告 `1BAD32D3...B7259`；R0063 再60/60但无 pending/stop，不补门 | R0064 独立 PID119388 包内 stop 30/60、paired save `761D36...8E92`/driver `0FC287...2A3`、进程回收；R0065 不同 PID60220 从该 pair cold 启动/同 actor+episode+战争目标、前16轮零重复 raise，但 turn17 自然事件 `stress_threshold_special.1001` 9 options 延展消费者缺失 RED，raw `FA25A1E4...649F43`，最后安全 pair `C58725E5...572273`/`1E8EC91F...9B3B3F`，CK3=0；不能称完整 cold continuation GREEN | `/root/event_inheritance` 先冻结原生事件树，`/root/war_gen034` 查现有 typed 口，必要最小事件消费者/只读输入后聚焦同版复验；R0059 grant-vassal reject-only 已进 master 但还缺真实后帧/下一 turn，不能因为 R0063 未遇提案就关闭 | PR #3 经官方检查 GREEN/rebase-only 合入，原/集成三临时分支/worktree 已即时清 |
| GOV 正式建设 | private consumer 首门误比 public/native 修订号的 B1 已静态修；正式动作待验 | default-OFF `native-auto-run --allow-private-construction-formal-trial` | GOV 原 `73dbd1c`→master `be53794`，native private ON DLL SHA `47196B7E...E171760` | R0060 20/20 只有 life-advance/战争评估/事件和 checkpoint，471 history 无建设 query/submit/receipt，产品证据不足；实际根因六次 native/public revision 3/4 等被旧同帧门错拒，新测试先 RED 后 normal/`-O` 各109 GREEN | R0060 pair date53181984 技术可恢复，但下次正式建设须从原 R753 pre-action pair 新 Z state、重绑定新 Python fingerprint，不能原样续无动作窗口 | `/root/governance_family` 已交付静态修复；新同版 construction typed/物质后帧/下一 turn/cold 仍缺，公共广告 OFF | PR #4 官方检查 GREEN/rebase-only 合入；原/集成两临时分支/worktree 已清 |
| Council / G2 | Council `1/4`、公共 OFF；权威 G2 `2/8` | 议会私有 action-OFF；G2 JSON 未改 | 保护 master `be53794`，PRV-005 冻结 `3da54dc` 不随它重标 | guest/pending/replacement-positive 不存在；自然继承、长期整局/双种子无新增完整证据 | 不适用 | 围绕已出现实证 B0 优先；不扩大宗教/广矩阵 | 已集成临时 branch 无遗留 |

当前单 CK3 实例 0，唯一活动轮次账本 `Z:\ck3_mod_rewrite_process_assets\g2-live-run-ids-v1` seq65。历史 raw RED、paired checkpoint 与 run metadata 独立保留；旧 C 临时源物理删除仍受工具政策拒绝，不称完成。

## 2026-09-22 当前覆盖：PRV-006 R0067–R0071

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| h1662 普通封建可运行预览 | **GO，仅此冻结起点/版本组合**；非整局 | 包内 `g2_preview_operator.py` → `native_auto_run` / `ck3_auto_turn` | [稳定 ZIP](Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-cad5518-20260922/release/g2-preview-ordinary-h1662-cad5518-prv006.zip) SHA `7503E5D92703F29EA9BF72009FB24A108EFEE914AE6DDE42BB1135D1A6952803`；agent `cad5518`、native `434f832`，2372 CRC/2371 解压 SHA GREEN | R0067 fresh eligibility；R0068 60/60 typed 征兵，army[]→[301989888]、下一 turn 消费；R0069 自然 grant-vassal 提案唯一 typed 拒绝、pending→null、下一 turn 消费；分支 R0071 自然 stress.1001 选择 native7、100→64、事件消失/下一 turn 消费，非同一主链 | R0069 包内 stop 19/60、成对 save `44793BF1...18838`/driver `0FE2FE95...98959`、PID163504 回收；R0070 新 PID44176 从此 pair cold 20/20，同 actor/episode，无重复 raise/reject，主链续存 `7C988B19...59A94`/`7983567B...76BD`；全树回收 | 任意存档/自然继承、战争终局、议会后三门、治理物质结果尚未验；`/root` 继续普通主链与 G2；未知强制状态留 RED | PR #5 原 `a67d3a1`→master `0171d3a`，三条临时 branch/worktree 清理；PR #6 原 `a703313`→master `826cad9`，两条清理 |
| GOV 建设物质源 | **RED 未关闭**；diagnostic 不是动作后置 | 私有读取/正式 consumer 仍 OFF | PR #6 master `826cad9` 保留 source_red payload；PR #7 pre-action 只读 query 原 `3248c9b`→master `87c8e20` | R0066 ACK pending 但 material source_red；仅原 R753 原始 pre-action pair 可安全只读探查；不得重复提交 | R0066 save 为旧 pre-action 而 driver 已记 pending，不可作为 paired cold restore | `/root` 与唯一实机 owner 聚焦 source；不把 ACK 称物质建设 | #7 原/集成两条远端与本地 branch/worktree 经 CAS 即时清理 |
| Council / G2 | Council 1/4 公共 OFF；权威 G2 **2/8** 未改 | 私有 gate；合同 JSON | 冻结 PRV-006 `cad5518`；后续 master 不倒填为其制品 | guest/pending/replacement fireability 真正正例未出现；自然继承与两种子整局未验 | 不适用 | `/root` 在普通 campaign 出现真实门时取同帧只读证据 | 不适用 |

当前已验 R0071 回收后 CK3=0，唯一可写 run-ID root `Z:\ck3_mod_rewrite_process_assets\g2-live-run-ids-v1` last sequence 71；R0072 普通主链续跑独占负责人另行记账。旧 R888/PRV-005 NO-GO 与 R0066 RED 都保留为历史真实状态；旧 C 临时源删除仍受工具策略限制，未称清完。

## 2026-09-22 R0072 新证据：历史 GO 不再可作为持续续跑广告

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRV-006 h1662 持续续跑 | **NO-GO 当前连续使用**；R0067–R0071 门仍历史有效，R0072 扩展窗口真实 RED | 同包 `g2_preview_operator.py run` | agent `cad5518`、ZIP `7503E5D9...952803` 未改；R0072 raw report `3D6D480350F3AE1D654821F953BDA0731E0A1C287122CE854EBD7D8777AD438B` | 从 R0070 main pair 正式续跑 4 attempted/3 successful turn，+23 游戏日/129.64 秒，自然 `health.7000` instance9、唯一 enabled native0、add infirm indicator；合同缺 scope_types/saved_scope_name_sets/native_option_indices/disabled_native_option_indices，四项检查 false，`registered_contract_projection_drift` RED，**没有提交选项**，不能称继续 GREEN | source save SHA `7C988B19...59A94` 仍原样，rebound driver `1FF57C1D...F7EE`，RED driver `87E54EFF...CE5E`，recoverable=true/invalidation=false；CK3 PID155176 全树回收，canonical ledger R0072 `completed-red` | EVT-B0-R0072 `/root/event_inheritance` exact 原版树与最小注册修复；重新冻结新候选、受影响同版复验后再决定 GO；旧 GO 收据仅记录当时范围 | 工作分支待提交；旧 ZIP 不改写 |

受控场景的实际吞吐仅 23 游戏日/2.1607 分钟≈10.64 游戏日/分钟（计启动与停顿），不推断长期速度；G2 仍 2/8、议会 1/4。不能把 R0072 RED 改称超时或换存档消失。

## 2026-09-22 R0073–R0074：PRV-007 候选未晋级

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| health.7000 真实事件闭环 / PRV-007 | 静态修复已集成、**live 自然事件未再触发，NO-GO** | 同包 `g2_preview_operator.py`→`native_auto_run` | [PRV-007 候选 ZIP](Z:/ck3_mod_rewrite/.task-tmp/PRV-007/candidate-h1662-b56c068-v2/g2-preview-ordinary-h1662-b56c068-prv007.zip) SHA `F4AEBC1B14810BDB1EF516DE568AD3C3561BEF0D4AA5412FDA0363C51B74A640`；agent master `b56c068`、native不变、CRC2375/fresh2374/no-launch | R0074 同包从 R0070 main safe pair 正式20/20，250游戏日/181.852s；未遇 health.7000 故不能证明 infirm 后置。自然 grant-vassal 两次 turn8/14 typed 拒绝、独立 pending 消失、turn9/15 消费，[证据清单](Z:/ck3_mod_rewrite_process_assets/g2-preview-prv007-r0074-main-green-20260922/evidence-manifest.json) SHA `A1EFE2F1...D9F1F9` | save `B836D93E...92683`/driver `4C7278F0...364D3` 成对，PID110208回收；同包 stop/cold R0075/R0076 另验 | `/root` 普通 campaign 机会性自然事件后置；R0072 原 RED 仍存，不对不可复现随机池重复试运气 | PR #9 `f5f9fca/b8faabe`→`8d780a0/b56c068`，原/集成 branch/worktree 即时 CAS 清 |
| GOV 原 R753 建设源只读诊断 | R0073 **prelaunch RED** 后已修 parser；实机 source 未读，R0066 material RED 未关 | private source-only CLI，world-action 不调用 | [R0073 evidence](Z:/ck3_mod_rewrite_process_assets/g2-gov-r0073-prelaunch-red-20260922/evidence-manifest.json) SHA `9AB32C74...1F35`；PR #10 master `0e251b2` | R0073 canonical `R0073` 被旧正则拒绝，CK3 未启动/零动作；新 FINAL R753 Z state no-launch READY 等唯一实例排队 | 原 R753 pair 仍旧哈希且无 pending；不能用 R0066 post-driver 搭旧 save 冒充 pair | `/root/governance_family` 修 parser，唯一实机 owner 后续只读一次；建设真实 action/postcondition 待另场 | `f139f1c→2ed0e5c→0e251b2`，原/集成 temp refs/worktree CAS 清 |

R0074 的 250 游戏日/3.0309 分钟≈82.5 游戏日/分钟仅为本次有界有效吞吐，不拿它承诺百年门；单实例当 R0075 启动时由唯一 owner 记当前轮次，R0073 ledger 已真实 `completed-red`。G2 JSON 分母与状态不变。

## 2026-09-22 R0075 自然继承：分配匹配但下一循环 RED

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 自然继承与同一 campaign 继承人续玩 / G2-M3 | **部分 live；下一策略循环 B0 RED**，M3 未完成 | PRV-007 `native_auto_run` successor 分支 | agent `b56c068`、DLL `DA06EF...F99`；[R0075 冻结证据](Z:/ck3_mod_rewrite_process_assets/g2-preview-prv007-r0075-natural-succession-red-20260922/evidence-manifest.json) SHA `42E8BDCDD598E82DC63FFB3855425EF6AB29F2F5CA14107C058A9DBA0DB9803D`，raw `62930516...48F6` | turn12 同 PID123012 玩家31853自然死亡→36403，预测继承人/头衔 `[524,525,530]` 分配 matched；turn13 正式 `query-current-timeline-blocker-context-v1` `unsupported native gameplay step`，零继承人后续 gameplay；planned stop 太迟非 stop 证据 | predeath save `0CE2...BF5C` 与 RED 后新 episode driver `40C3...E569` 不成对；无 postdeath save；最后冻结有效 pair 仅 R0074 `B836D93E...92683`/`4C7278F0...364D3`，PID回收/ledger completed-red | INH-B0-R0075 `/root/event_inheritance`：C++已有 handler 却被默认 OFF 宏裁掉，新 exact DLL ON + minimal builder capability guard + 真 successor query/下一 turn 实机；不禁用查询 | 原 PRV-007 候选未晋 GO；新工作包 branch 在途 |

R0076 编号用于后续独立 GOV 原 R753 pre-action source-only probe（R0075 后拟 cold 方案已因 RED 取消且从未分配 R0076）；只读结果出来再记，不能预填。权威 G2 2/8 不变。

## 2026-09-22 R0076 治理只读查询实际结果

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GOV 原 R753 动作前建设源诊断 | **RED**；private 恢复谱系核算错误 + 原生 checks 截断/成本与动作仍不就绪；R0066 material RED 保持 | `native-query-private-construction-source-v1` | final master `0e251b2`、private ON native `47196B...1760`；[R0076 frozen evidence](Z:/ck3_mod_rewrite_process_assets/g2-gov-r0076-source-query-red-20260922/evidence-manifest.json) SHA `67B243AF2212511C4F093F55EBFE7427ED324CCF1632A43C6F40F2A531743B72` | native selected barony2103/province2635/building24/slot1，stock cost15000000/gold50035659；`checks_truncated=true,cost_ready=false,construction_action_ready=false`，没有建设提交/日期推进，不能推断建成 | source save `D8BDC3...01474` 未变，PID168780回收；diagnostic `single_cold_restore=false` 因既有 restore 谱系合法保留行+本次新行而误判，ledger completed-red | GOV-B0-R0076 `/root/governance_family` 仅修 private diagnostic 与聚焦验证；真实原生未就绪/动作后 material 仍独立待解 | 工作分支待交付；不重试原查询 |

CK3 R0076 后 0 个存活实例；新 exact native death/succession 宏 ON DLL 与后续 frozen candidate 尚在施工，不冒充可运行预览。G2 JSON 仍 2/8。

## 2026-09-22 R0077：G2-M3 可见结果完成，PRV-008 仍待 stop/cold

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标准封建自然继承 / G2-M3 | **complete；G2 3/8**，不等于整局/两种子 | PRV-008 `g2_preview_operator.py`→`native_auto_run` | ZIP `B9952E54...ECC2BD9F3`、agent `ca852d1`、DLL `B114FD8E...29FA8`；[R0077 冻结证据](Z:/ck3_mod_rewrite_process_assets/g2-preview-prv008-r0077-natural-succession-green-20260922/evidence-manifest.json) SHA `28F94B1E1C0BFFFF4A43CA8085B18FD4E8966872CB6DADEBC0A307B22BDF6D67` | 60/60，turn20 同 PID65096 玩家31853自然死亡→预期36403，头衔 `[524,525,530]` matched；turn21 typed timeline query→一次 typed close `materially_verified`，继承人后续正式 turn21–60含互动、婚姻、事件、日期 | R0077 末尾成对 save `39828127...2BEF`/driver `5B1B9410...ADFB`；进程回收；**本包 cold 尚未完成** | preview 同包受控 stop R0078、新 PID cold R0079 由 `/root/runtime_preflight` 独占；R0072 health 修复后自然后置仍不足 | PR #12 原 `bbf64d3`→master `ca852d1`，先前清理已核验；PR #13 private diagnostic 原 `b89009f`→master `1c1e0a9`、两组 temp refs/worktrees 清 |

Council 仍 1/4、公用 query/action OFF；GOV R0066 物质 RED 未关闭。R0077 329 游戏日/268.717 秒仅为有界实际吞吐；当前预览持续交付 **NO-GO**，不得将静态新 ZIP 直接交付为可持续自动游玩。

## 2026-09-22 R0078–R0079：预览实机最小门齐，稳定交付已 GO

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRV-008 标准封建继承人受控预览 | **可运行预览 GO，仅声明的 exact 主机/配置及 R0078 后继承人配对点的20-turn窗口**；非整局 | [稳定用户指南](Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-ca852d1-20260922/START-HERE.md)→包内 `g2_preview_operator.py`→`native_auto_run` | [ZIP](Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-ca852d1-20260922/release/g2-preview-ordinary-h1662-ca852d1-prv008.zip) SHA `B9952E54...ECC2BD9F3`/agent `ca852d1`/DLL `B114FD8E...29FA8`；[交付清单](Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-ca852d1-20260922/release/DELIVERY-MANIFEST.json) SHA `49DA2BBA...BC744C`；fresh payload 2374+manifest、stable R0078 pair no-launch、交付12/12及原始证据9条 SHA GREEN | R0077 typed继承窗 Close→独立清窗/下一 turn；R0078 新互动 typed拒绝→下一 turn查空；R0079 20/20无新 typed、不重放旧动作；包内 h1662 sample 仅静态准备 | [R0078 stop](Z:/ck3_mod_rewrite_process_assets/g2-preview-prv008-r0078-stop-green-20260922/evidence-manifest.json) SHA `B98A6BEF...7741D`，PID92204、默认 pair `764E101E...A8517D`/`468B512B...667B97`；[R0079 cold](Z:/ck3_mod_rewrite_process_assets/g2-preview-prv008-r0079-cold-green-20260922/evidence-manifest.json) SHA `72033891...EFD6F`，新 PID126124、20/20、pair `2AB80577...E6CF8F`/`B057FCB8...DEB02`；全进程回收 | 范围外/未知按原合同停止，不宣称无限/任意存档；R0072 健康事件修复后自然后置仍待观察 | PR #12 原/集成已清，PR #15 G2-M3 原 `fc67bb1`→master `be3b21e` refs/worktree 清 |
| GOV R0066 ACK 后配对恢复 | 静态 B0 修复已合入，建设物质 **RED** 未闭合 | private formal `native-auto-run` | PR #16 原 `d798758`→集成 `9709f92`→master `573f742`，normal/`-O` 各95/95 | ACK 后 fence 仅声明 `material_postcondition=unobserved`；R753 有效原 pair 正排 GOV-LIVE-05，不重复旧不明动作 | checkpoint 与 pending request ID 同步的 fixture GREEN，实机 fence/主动 construction 仍待验证 | `/root/governance_family` 独占下一 CK3 有界20/900/300；保留任何 RED | #16 原/集成临时 refs/worktree CAS 已清 |

M5 五候选源树 PR #17 原 `d9f231c`→master `b0d91b9` 已核对并清临时引用；M5 read-only bridge/MCP 尚在隔离开发，公共/动作广告 OFF。G2 权威仍 3/8、Council 1/4；R0079 后唯一 CK3 owner 已移交 GOV-LIVE-05。

## 2026-09-22 R0080：建设物质可见但正式收据 RED

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 私有建设完成/治理 G2-M4 的建设分支 | **R0080 RED 保留**；实际 active 建设与精确扣费仅为部分物质证据，未由正式下一循环消费 | `native-auto-run --allow-private-construction-formal-trial` | protected agent `573f742`/GOV private DLL `47196B...1760`；[冻结 R0080](Z:/ck3_mod_rewrite_process_assets/g2-gov-r0080-red-20260922/evidence-manifest.json) SHA `551920217FE0EC4167CAA17E9FDAA4DCE6F966B539F77F0305D63660D0D42213` | 唯一 typed submit/ACK pending；独立 native active tuple 2103/2635/24/1、initiator29829，gold50035659→35035659，原生费用15000000；Python 收据错误要求动作后新候选 cost sample，`source_red` 停止；没有后续正式消费 | ACK 后相邻 history446→447 paired save `1928BD74...0CBAE`/driver与 pending ledger 保留，`recoverable_from_checkpoint=true`，PID33820回收；**禁止从 R753 再提交** | GOV-B0-R0080 `/root/governance_family` receipt-only 解析 `e65563f`→集成候选 `ef4fe14`/PR #20，normal/`-O` 各13；保护合入后从 R0080 pair 新 PID cold +下一 turn验证，公共 OFF | PR #20 在保护检查中，原/集成临时 refs/worktree 待完整集成才清 |

M5 不广告：PR #18 read-only literal 已合入 master `b7a76e9` 并清临时 refs/worktrees；R736 新 literal 无 paused live，旧 driver 缺配对 checkpoint，不能计 G2-M5。PRV-008 稳定预览仍仅自身 exact 支持范围 GO，G2 权威 3/8。

## 2026-09-23 R0164 Robert 防御战争围城续行增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0162 解围到达后围城续行 | **R0164 有界 GREEN**；战争终局未闭合 | `g2_preview_operator.py` → `native_auto_run` formal 60 | Python source `cb43a50`，集成 master `54a39e1`；[R0164 冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0164-siege-progress-green-20260923/R0164-final-frozen-pair/R0164-pair-freeze.json) SHA `624D76BEA1823A8AEB67DE6959B97029B6B4416B3531C4B26083A2A7099C2D0E` | 60/60，1 个 committed route sentinel，22 个 siege-progress gameplay turns；army `83886367` 在 `2627` sieging，target null/route[]；WarID `16777250` / `95` active `-7/-8`，title/domain 稳定 | R0162 h989 official cold → R0164 h1082/raw53190528 成对 checkpoint；save `C2E8778D...F7E2` / driver `3024D5CE...C799`；+34 持久日，Robert 1,925/36,524；cleanup proven | 继续有界正式围城直到独立占领/战争终局或新 exact blocker；`/root` 唯一 CK3 owner | 报告分支待 PR 集成；运行资产保留 |
| R0163 / R0165 非产品轮次 | R0163 `voided`；R0165 `completed-red`，均无日期积分 | R0163 启动前拒绝；R0165 no-launch 后外部对话中断 | R0163 预建输出目录；R0165 formal report 0 bytes，现场保留于 `g2-robert-r0164-siege-progress-master54a39e1-20260923/live-R0165` | R0163 无 CK3 接触；R0165 曾启动 PID155452，但动作/日期/checkpoint 均 0 | R0165 save/driver 仍处于 R0164 h1082 prepared 配对，受管进程与 owner 已回收；R0166 从不可变 R0164 pair 新轮次恢复 | 仅外部中断，不当作围城策略失败；`/root` | R0163/R0165 现场与 R0164 冻结配对保留 |
| R0166 二次冷恢复围城证据绑定 | **RED**，5 次尝试/4 次成功只读查询，0 gameplay/date | official restore → formal `native_auto_run` | [R0166 冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0166-restored-siege-observation-red-20260923/R0166-final-frozen-pair/R0166-pair-freeze.json) SHA `1782D61B62BD3E32B533344808B002FE056ED23D097C3E5BF5200A77E2E56A70`；source master `54a39e1` | planner `native_war_defender_siege_relief_observation_blocked`，要求 `accepted-native-move-arrival-for-current-siege`；两战 active `-7/-8` | official cold restore R0164 h1082/raw53190528 成功，但 planner 未绑定跨第二次恢复的到达围城证明；save 不变 `C2E8778D...F7E2`、RED driver `4D6BB936...7F53`；cleanup proven | 修 exact 多次恢复证据绑定并从合法配对有界复验；`/root` | R0166 RED 现场和原 R0164 冻结配对均保留 |

PRV008 冻结预览 GO 与资格边界不变；G2 **3/8**（M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started）。百年、首整局、独立种子仍为 **0/1、0/1、0/2**；Robert **1,925/36,524** 只表示本主线持久日期跨度。

## 2026-09-23 R0167 M4 Robert 生活方式同帧只读

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4 生活方式 current/focus/perk readback | **private read-only GREEN**；typed 闭环与公共广告 OFF | `private-query-player-lifestyle-current-state-v1`、`private-query-player-lifestyle-stock-focus-v1`、`private-query-player-lifestyle-formal-v1` | [R0167 冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-m4-robert-r0167-three-query-green-20260923/R0167-evidence-freeze/R0167-readback-freeze.json) SHA `AEAB84B6BDD6548685FC89757675CEBB7BD05532EE6AA984CE373B559B9259D3`；8 个原件哈希/只读核对 GREEN；report SHA `890D0D09...21BA78`；Python `37ff65f`、native `752c5eb` | Robert actor29829、`h1082/raw53190528`、paused `native:3` 三查询；当前财富 focus、stewardship XP 2131.25、未用/已用 perk 点 2/4；唯一 policy-target final-legal `cutting_corners_perk`；0 typed/gameplay/date | 原 R0164 save SHA `C2E8778D...F7E2` 未变；PID177600、watchdog/owner 回收，进程0；Robert 持久 1,925/36,524 | 源配对两场 active defensive wars；现有 consumer 仅在独立同帧 `at_peace` 封建证明后可提交。后续合法场景需 typed perk、独立后置、下一 turn 和恢复证据；M4 in progress，`/root/m4_prep` | 本报告分支待 PR 集成；冻结原件保留 |

PRV008 窄范围 GO；G2 **3/8**，百年/首整局/独立种子 **0/1、0/1、0/2** 均不变。R0167 只证实本次私有读取，不关闭 R0166 战争恢复 RED。

## 2026-09-23 R0168 Robert h1251 战争连续运行增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0168 三战续行 | **116/117 后产品 RED**；Robert 持久 1,999/36,524（+74），战争终局仍 open | R0164 h1082 official cold → `native_auto_run` formal120 | source `b153c47`；[R0168 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0168-new-siege-binding-red-20260923/R0168-final-frozen-pair/R0168-raw-freeze.json) SHA `C9AA22723EA96127312F78A647660DA49AC1411BABE8C389B15F5E0C4EEA7FAD` | query75/gameplay41，h1251/raw53192304 已保存；三防御战 `16777231/16777250/95` active `0/+29/-4`，army83886367 在2638 combat；第117帧 `single-idle-controllable-army-binding` RED，无战争终局 | save `C21E5940...ED9CA`，raw driver `14207EC4...AE03` 有 h1252/h1253 两条只读尾，尚需官方语义恢复；五原件只读，受管进程/owner 回收 | 战斗态军队绑定与同帧观测；`/root`，后续从官方恢复的 h1251 候选验证 | 原始冻结与运行证据保留；本报告分支待集成 |
| h1251 恢复与战争修复候选 | 旧 `3c75e06` **no-launch GREEN**；新 `13b356a` **待实机** | official prepare/rebind/preflight；正式新轮次尚未发生 | [旧基线清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0168-h1251-recovery-master3c75-20260923/CANDIDATE-BASELINE-NO-LAUNCH.json) SHA `81C0DB79...4477C5E92`；[PR #154](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/154) `13b356a` 官方 static/CLA GREEN、截至10:30仍 OPEN | 旧基线 0 CK3/gameplay/date；新版候选已有 preflight ready，尚无 typed/下一 turn/战争物质结果 | 官方匹配冷恢复语义保留 h1251、仅裁 h1252/h1253 查询尾；旧 prepared driver 未物理裁切、cold 未实机提交；新代码须独立固定并复验 | 新版候选完成必要 no-launch 后排唯一 CK3；`/root/r0168_recovery_pair` 与唯一 owner | PR #154 待保护 rebase/集成后清理；候选资产按身份保留 |

[PR #157](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/157) `1651713` 将 R0167 私有只读与 R0168 raw RED 写入权威状态投影，官方检查已过、截至10:30尚待集成；与本台账文字包独立。PRV008 原 ZIP 及资格不变。G2 **3/8**，百年/首整局/独立种子 **0/1、0/1、0/2**；历史 Murchad 14,900 日不并入 Robert。

10:34 状态增量：PR #154 已快进合入 `master@13b356a`，其源码清理待核；PR #157 仍 OPEN。R0169 唯一实例已启动，正式战争结果未知。候选代码集成不改变 R0168 产品 RED。

## 2026-09-23 R0169 h1333 正式续行增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 三战正式续行 | **78/79 后产品 RED**；Robert 持久 **2,088/36,524**（+89） | R0168 h1251 official cold → `native_auto_run` formal120 | source/master `13b356a`；[R0169 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0169-siege-arrival-red-20260923/R0169-final-frozen-pair/R0169-raw-freeze.json) SHA `A7E9E701454998B52E755AEB767DE4CD94C9F3B152AC473772BB5F35F8105F97` | query61/gameplay17；末帧三防御战 `16777231/16777250/95` 比分 `0/-7/+52` 仅为观察；`accepted-native-move-arrival-for-current-siege` 新 RED，无终局 | h1333/raw53194440 save `2B8933FC...7F98A`；raw driver `81B7AB33...F1A4A`，末端 raw53194848 的 17 日未保存，不计持久；五 copy 只读、清单只读属性待补，进程/owner 回收 | 官方恢复 h1333、核对同帧到达与安全路线，最小修复后正式消费；`/root` | 原始证据保留；PR #154 已合入，源码清理由协调者核验 |

PRV008 有界预览 GO 与 G2 **3/8** 保持；百年/首整局/独立种子 **0/1、0/1、0/2**。历史 Murchad 14,900 日独立记账。R0169 的 +106 日只是末端观察，本轮正式可接续的持久增量为 +89 日。

## 2026-09-23 R0170 h1333 冷恢复增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 围城到达绑定续行 | **15/16 后产品 RED**；Robert 持久仍 **2,088/36,524**，新增持久日 0 | R0169 h1333 official cold → `native_auto_run` formal120 | source/master `fe81e43`；[R0170 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0170-siege-arrival-red-20260923/R0170-final-frozen-pair/R0170-raw-freeze.json) SHA `3DE132AFB6404933CBBF452AE0F653EC0F1B55B8D44FA6B357FA1DF2F5350499` | 13 query/2 gameplay/0 checkpoint；末帧 raw53194872 只属观察；`accepted-native-move-arrival-for-current-siege` 仍 RED，无战争终局 | h1333/raw53194440 save SHA `2B8933FC...7F98A` 未变；新 raw driver `C456145D...71D72` 在保存点后有记录，待官方恢复；新 PID 已回收、owner 释放 | 核到达意图与同帧围城目标，再最小修复与正式后置；`/root` | 冻结清单与五 copy 只读保留；源码分支清理由协调者核验 |

R0170 末帧相对 h1333 的 18 日和累计观察 2,106 日不重复累计到 R0169 已保存的 2,088 日。PRV008 有界 GO、G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 不变，M4 仍仅私有只读。

## 2026-09-23 R0171 同 checkpoint 路线观测增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 当前路线意图绑定 | **5/6 后产品 RED**；Robert 持久 **2,088/36,524**，新增持久日 0 | R0169 h1333 official cold → `native_auto_run` formal120 | source/master `2100ee2`；[R0171 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-r0171-route-intent-red-20260923/R0171-final-frozen-pair/R0171-raw-freeze.json) SHA `310B27C52E7FD03978A02536B241A0DE37371EDC227281F90EEDC40188096972` | 5 query/0 gameplay/0 checkpoint/date；同帧三战比分 `0/-58/+51`；`complete-matching-active-native-move-intent-route` 新 RED，路线因果待查，无战争终局 | h1333/raw53194440 save SHA `2B8933FC...7F98A` 未变；raw driver `FBE3A287...DD177` 待官方恢复检查；进程/owner 回收 | 核重复同 checkpoint restore 与同帧 active move intent route，明确观测或最小修复；`/root` | 冻结清单及五 copy 只读保留；源码分支清理由协调者核验 |

R0170 的 raw53194872 未保存观察不累计至 R0171。PRV008 有界 GO、G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 不变；M4 仍仅私有只读。

## 2026-09-23 R0172/R0173 恢复生命周期增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0172 snapshot-only 入口 | **prelaunch fingerprint RED**；CK3 contact/snapshot/action/date 均 0 | prepared ordinary/xar_off → CLI native-session | [no-launch 诊断索引](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0172-h1333-master0342-snapshot-lifecycle-fix-20260923/checks/R0172-LIFECYCLE-FIX-NO-LAUNCH-INDEX.json) SHA `09B12B88F48D0CE0711C9A66FEB49FF683A4738A72F1B99EEEFBF97751F27525`；source `0342cd8` | CLI 漏传 `prepared_xar_enabled=xar_off`，native-session 默认 xar_on；未接触 CK3 | h1333 save 不变；修正入口离线清单 SHA `3F64AACE...CEA07`，不等于 MCP ingest GREEN | 显式绑定 profile/lifecycle 并验受影响字段；`/root/r0168_recovery_pair` | 候选和失败证据按身份保留 |
| R0173 MCP ingest | **harness RED**；无 paused snapshot/动作/日期；战争产品 RED 未重测 | `0342cd8` 冷 CK3 PID74152 → MCP | [原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0173-mcp-lifecycle-red-frozen-20260923/R0173-final-frozen-pair/R0173-raw-freeze.json) SHA `F19A62FF60C1873067E5FF6BE487F97832F5AAE049E9CD0DC3794602D069B71A` | native-session ready 后 pipe ingest 因 persisted lifecycle 与 frozen profile 不同失败；stop/shutdown/进程/owner 回收 | save h1333/raw53194440 SHA `2B8933FC...7F98A`，raw driver `E5A3C101...23B18` 未手改；Robert 持久 2,088/36,524 | 补 MCP lifecycle 同帧绑定与 paused snapshot；`/root/r0168_recovery_pair` | 15 文件暂未设只读，冻结负责人待封存；源码分支状态由协调者核验 |
| R0173 后续 no-launch 候选 | prepared/preflight **ready**；MCP live pending | official prepare/rebind/preflight，0 CK3 | [preflight](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0173-h1333-master0342-mcp-lifecycle-fix-20260923/state/preflights/20260923T034253Z-one-generation-preflight-35c35d02/report.json) SHA `EC49C6DB049A823A61E0FE8DC2F1907D1943E230A9D23DF5A21CA0406526C566` | 无新 paused readback | 同一 save h1333、prepared driver `715ACC4A...638F473`；旧 raw 和新 prepared 各自保留 | 验 MCP ingest，再排唯一 CK3；`/root/r0168_recovery_pair` | 独立候选资产保留 |

[PR #163](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/163) 为 M4 战时 perk checkpoint 候选，官方 static 已通过、实机 typed/perk 闭环未取得；它不替代 R0174 的 MCP 只读证据或战争后置。PRV008 有界 GO、G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 不变。

## 2026-09-23 R0174 路线只读观测增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MCP 生命周期与 native route 读回 | **私有只读 GREEN**；战争 OODA 仍 RED | R0173 新 prepared h1333 → R0174 paused snapshot `native:3` | [观测索引](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0173-h1333-master0342-mcp-lifecycle-fix-20260923/read-only-mcp-probe-R0174/observation-index.json) SHA `4BC100E01ED068DE094EEEA94FB99B3228635BB6E14BEE432ECA3D77E10B9269` | actor29829、date53194440、army83886367 当前2624→目标2619、native route `[2619]`，0 typed/date；进程/owner 回收 | save仍 h1333/raw53194440、Robert 持久 2,088/36,524；R0172/R0173 RED 原件保留 | 正式策略在有效帧消费 route，并验证动作/后置；`/root/r0168_recovery_pair` | 只读证据保留，代码集成/源码清理由协调者核验 |

R0174 只解除该候选的私有 MCP/route 读回缺口；战争产品 RED、M4 公共 OFF、PRV008 有界 GO 与 G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 不变。

封存后续证据：[R0173 15/15 只读复核](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0173-mcp-lifecycle-red-frozen-20260923/R0173-seal-verified.json) SHA `4C521BDBDC4CC9470090F47A92977336F57ED32A86D888CAC3466BD79A8E0226`，原 freeze SHA 不变；[R0174 24/24 冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0174-snapshot-green-frozen-20260923/R0174-final-frozen-pair/R0174-raw-freeze.json) SHA `9D727162162AF9FE65430D8ED2BB77AB8422C704FF15390A8585909F90226FF0`，seal SHA `CA10F99FA6FDA55C0A64FA15C2D1CFC931D2858D540019A8136A23F10E498BFF`；driver `D594512C...F823DE`，官方下一 pair 边界 `1336→1336/drop0`。这些是运行资产，随源码分支清理保留。

PR #163 已快进合入 `master@f8dc408`、源码分支/worktree 清理完成；M4 战时 perk runner 仍待同版本实机 typed/后置/下一 turn 验收，公共能力 OFF。

## 2026-09-23 R0175 M4 战时 perk 私有实机增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4 wartime perk typed trial | **RED / 游戏动作结果未知**；公共 query/action/ad OFF | 已合入 `f8dc408` 私有 runner；R0174 h1333 官方配对，`ordinary_campaign_succession/xar_off` | [R0175 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-m4-r0175-wartime-perk-red-frozen-20260923/R0175-final-frozen-pair/R0175-raw-freeze.json) SHA `E8BC9D5C81CB36AAE36865F3B05D7DAB003EF52F04EBBB8A182B2809455A441E`；[report](Z:/ck3_mod_rewrite_process_assets/g2-m4-r0175-wartime-perk-red-frozen-20260923/R0175-final-frozen-pair/report.json) SHA `42A80DF4...670D88B` | driver #1340 `action_state_unknown`、#1341 同一请求 native ACK `submitted_verification_pending`；等后续 paused frame 603.8 秒超时，无独立 `HasPerk`/点数、下一 turn 或动作后 checkpoint | save h1333/raw53194440 SHA `2B8933FC...7F98A` 未变；raw driver `D34E3D26...F073` 有 #1338–#1341 四条后续记录；[no-launch 语义复核](Z:/ck3_mod_rewrite_process_assets/g2-m4-r0175-wartime-perk-red-frozen-20260923/R0175-semantic-audit.json) SHA `54CFA955...279618` 指向原 R0174 干净配对，官方恢复后新暂停帧须先核 perk/点数，不能盲重试；进程/owner 0 | M4 动作后置及下一 turn；`/root/r0168_recovery_pair` 与 M4 owner；战争策略 RED 独立 | `f8dc408` 源码分支已清；R0175 九份只读冻结资产长期保留；本状态/报告包独立待集成 |

Robert 持久 **2,088/36,524**，G2 **3/8**，百年/首整局/独立种子 **0/1、0/1、0/2**；PRV008 原有界 GO 与战争产品 RED 均不变。本包没有启动 CK3。

## 2026-09-23 R0176 h1439 正式战争续行增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Robert 三防御战续行 | **84/85 后产品 RED**；Robert 持久 **2,135/36,524**（+47） | R0174 h1333 official cold → `native_auto_run` formal120，source `1f10991` | [R0176 原始冻结](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0176-war-red-frozen-20260923/R0176-final-frozen-pair/R0176-raw-freeze.json) SHA `43DD72993C218E07AC15EFAC191312CB40DB15795E71208812465E4BB18F8421`；formal report SHA `3411FA75...DCF9AE` | 63 query/21 gameplay/6 checkpoint；旧 active-route RED 有界越过；第 85 turn 新 `single-idle-controllable-army-binding` RED，`sieging`+完整 route 分类待修；三战仍 active，未保存末帧比分 `-13/-5/+54` 不冒充持久状态 | h1439/raw53195568 save `71DA84C7...7A41A4A`；raw driver `7AAB1609...CA251A0`；第 48 天 raw53195592 未保存；[语义审计](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0176-war-red-frozen-20260923/R0176-semantic-audit.json) SHA `1347EAA6...85C9420C6` 说明 #1440–#1448 须官方恢复；清单及 10 copy 只读，进程/owner 0 | 最小修复同帧围城军队/路线分类，再从 h1439 合法配对复验；`/root` 与战争代理 | 原始运行资产保留；本状态/报告分支待集成 |

PRV008 原有界 GO、G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 与 R0175 M4 public OFF 均不变；本包未启动 CK3，战争代码候选不预填 live 通过。

## 2026-09-23 R0177/R0178 双段有界续行增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0177 Robert 三战续行 | **有界 120/120 GREEN**；Robert 持久 **2,227/36,524**（+92） | R0176 h1439 official cold → formal120；source `8c0494e` | [冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0177-war-green-frozen-20260923/R0177-final-frozen-pair/R0177-raw-freeze.json) SHA `E77311A6...7C8182`；[语义审计](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0177-war-green-frozen-20260923/R0177-semantic-audit.json) SHA `F0AB6EF3...58266F4` | query90/gameplay30/checkpoint10；无 blocker；三防御战仍 active，无新增领土证据 | h1599/raw53197776 save `956B38E7...7763C7`、driver `AC8154F0...AA4BD8`，官方 raw/retained1599/drop0；进程/owner0 | 继续正式主线，从 clean h1599；`/root` | 运行资产保留；本状态/报告分支待集成 |
| R0178 两战胜利及剩余战续行 | **有界 120/120 GREEN**；Robert 持久 **2,410/36,524**（再+183） | R0177 h1599 official cold → formal120；source `8c0494e` | [冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0178-war-green-frozen-20260923/R0178-final-frozen-pair/R0178-raw-freeze.json) SHA `6AC64055...DD63A1C`；[语义审计](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0178-war-green-frozen-20260923/R0178-semantic-audit.json) SHA `BE5B9960...6517180` | query81/gameplay39/checkpoint11；WarID95 与 16777250 typed `enforce-demands` 返回 `victory_enforced`，独立 after-frame 各移除、后续 turn 消费；终帧仅 WarID16777231 active；titles/domain 未变、无本轮新增领土证明 | h1767/raw53202168 save `62786703...4EB05`、driver `E01A77CE...E2549`，raw/retained1767/drop0；进程/owner0。最后比分 -41 是 h1767 前 raw53201952 读回 | 剩余一战及继续整局，后续从 clean h1767 新候选；`/root` | 原始证据、checkpoint 保留；本状态/报告分支待集成 |

两段日期按 `h1439→h1599` **92 天**、`h1599→h1767` **183 天**各计一次；累计 Robert **2,410/36,524**。PRV008 有界 GO、G2 **3/8**，百年/首整局/种子 **0/1、0/1、0/2** 不变；M4 公共能力仍 OFF。本包未启动 CK3。

## 2026-09-23 R0179 M4 同日 perk 私有闭环增量

| 交付门/能力 | 状态 | 正式入口 | 制品/commit | 实机与下一循环证据 | 恢复证据 | B0/B1 缺口/负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cutting_corners_perk` 战时加点 | **私有 primitive GREEN**；M4 in progress、公口 OFF | R0178 h1767 official cold → `e0b7713` 私有 runner；ordinary/xar_off | [R0179 冻结](Z:/ck3_mod_rewrite_process_assets/g2-m4-r0179-perk-green-frozen-20260923/R0179-final-frozen-pair/R0179-raw-freeze.json) SHA `D8C63082...E21CC0`；[report](Z:/ck3_mod_rewrite_process_assets/g2-m4-r0179-perk-green-frozen-20260923/R0179-final-frozen-pair/report.json) SHA `A586D305...545493B`；DLL SHA `3F527D84...9E2D0A` | typed perk receipt `applied`、独立 HasPerk=true；unspent2→1/used4→5；后续正式 one-life 策略消费 receipt 并继续剩余 WarID16777231 的查询；0 日期推进 | 同日 h1774/raw53202168 save `8014519B...4B592`，raw driver `D097CA8D...DAF4B1` 在 checkpoint 后有 #1775 只读尾、需官方恢复；11 copy 只读，进程/owner0 | M4 后续 focus/perk 和治理闭环仍需独立门；战争仅剩一战 active；`/root` 与 M4 owner | 运行资产保留；本状态/报告分支待集成 |

R0175 旧同请求待确认 ACK 的 RED 不倒写成已通过；R0179 是后续新源码/实机的私有阳性。Robert 持久 **2,410/36,524**、PRV008 GO、G2 **3/8**、百年/首整局/种子 **0/1、0/1、0/2** 均不变。

## 2026-09-23 R0180 罗贝尔有界正式续行增量

| 交付缺口 / 能力 | 状态 | 正式入口 | 制品 / commit | 实机与后续消费证据 | 恢复证据 | B0/B1 缺口 / 负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0180 Robert 剩余防御战续行 | **有界 120/120 GREEN**；Robert 持久 **2,703/36,524**（+293），战争仍 active | R0179 h1774 官方配对冷恢复 → formal120；source `e0b7713`；ordinary/xar_off | [冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0180-war-green-frozen-20260923/R0180-final-frozen-pair/R0180-raw-freeze.json) SHA `878F7F6E...505D8851`；[语义审计](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0180-war-green-frozen-20260923/R0180-semantic-audit.json) SHA `CA4AE8C9...A864DA` | query80/gameplay40/checkpoint13；唯一 `religious_interaction.1020` 通知选项经 exact-build 脚本证实无选项效果，独立后置及下一 turn 消费；WarID16777231 仍 active，titles/domain 未变，无本轮新征服 | h1945/raw53209200 save `E80D43FE...A98131A`、driver `67150A63...370C2`；raw1948 的3条只读尾由官方投影 retained1945，原件未裁切；进程/owner0 | 继续最后一场防御战及主线；无通用宗教策略资格；`/root` | 冻结运行资产保留；本状态/报告分支待集成 |

R0180 增量不重复累计 R0179 同日存档；PRV008 有界 GO、G2 **3/8**，百年/首整局/种子门 **0/1、0/1、0/2** 不变。

## 2026-09-23 R0181 罗贝尔再续行增量

| 交付缺口 / 能力 | 状态 | 正式入口 | 制品 / commit | 实机与后续消费证据 | 恢复证据 | B0/B1 缺口 / 负责人 | 分支清理 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R0181 Robert 剩余防御战续行 | **有界 120/120 GREEN**；Robert 持久 **2,983/36,524**（再+280） | R0180 h1945 official cold → formal120；source `e0b7713`；ordinary/xar_off | [冻结清单](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0181-war-green-frozen-20260923/R0181-final-frozen-pair/R0181-raw-freeze.json) SHA `11B4F972...40CB712E`；[语义审计](Z:/ck3_mod_rewrite_process_assets/g2-robert-r0181-war-green-frozen-20260923/R0181-semantic-audit.json) SHA `F6AA961A...BEFAB1BF0` | query80/gameplay40/checkpoint14；40 gameplay均为 WarID16777231 七日目标守候；终帧战争仍 active，titles/domain 未变、未证明新征服；-16 是 h2120 前查询 | h2120/raw53215920 save `266D6F02...85756F0A`、driver `9AA47032...07922A`；官方 raw/retained2120/drop0；进程/owner0 | 剩余战争仍待合法终局，继续标准封建主线；`/root` | 冻结运行资产保留；本状态/报告分支待集成 |

R0180 +293 与 R0181 +280 各计一次，Robert 累计 **2,983/36,524**；PRV008 有界 GO、G2 **3/8**、百年/首整局/种子门 **0/1、0/1、0/2** 不变。
