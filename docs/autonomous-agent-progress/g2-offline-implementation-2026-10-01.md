# G2 后台实施账本：2026-10-01

真实开始记录时间：2026-10-01T14:33:47+08:00。用户明确要求继续并提高并行，且不得占用 CK3。基线为 `9e37d3df4227578fb754d71278810c9492ca948b`，施工树 `Z:/ck3_mod_rewrite/.task-tmp/g2src`；旧 migration 与范围核对树保持冻结。本页承接[八项施工图](g2-offline-work-map-2026-10-01.md)，记录实际施工与交付，不将计划当作完成。

## 15:22:18 用户调整后的当前范围

用户已明确允许本机CK3实机，并解除宗教研究暂缓，同时要求停止战争相关研究。WAR-CASH/PREWAR所有子线程已停止；已验证历史和失败artifact保留，不继续future cash、参战、集结或供给来源研究。尚未验证的prewar mailbox/supply草稿从当前candidate排除，不能沿用早期两步fixture的GREEN或其错误static-ready标签。Family已完成alliance历史冻结；当前新family query只消费子代House与退婚terms。

宗教当前新线程沿1.20原版数据与exact原生链研究Rite/Faith/Religion及最终判定，不开展战争分支。非战争council/faction/gift/Sway/law/Feast/prisoner/GOV与目标记忆继续集成。实际游戏由root串行操作，其它源码线程仍只做文件/fixture，首次新snapshot与材料结果以前不升级live。早期全程禁止CK3及宗教暂缓的段落是当时边界，当前以本段新用户指令为准。

15:12:37实际inventory显示本机无CK3，Steam在15:20:26已完成原生窗口可逆位移与新像素证明，并经人工图像审阅明确显示“Steam当前处于离线模式”和“上线”按钮；未点击上线。首轮环境missing psutil为environment RED，已在同一项目解释器补齐必要live依赖，未修改产品代码。初次fresh-frame输出目录未创建为harness错误，随后同一入口完成。准确输入/哈希在 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/live-preflight/`。

## 当前施工

| 工作包 | 实际范围 | 初始状态 | 实机边界 |
| --- | --- | --- | --- |
| M4 council | 新版候选、四类最终 gate、typed 任命与独立读取 | 正在实现 | paused 候选/门互证、任命后置及 next/cold |
| M4 faction | 完整身份、成员、原生 power/discontent/danger | 正在实现 | 真实派系同帧查询 |
| M4 gift | 原生最终发送、费用、好感预览、typed 操作 | 正在实现，依赖 faction | 合法接收者及 gold/opinion 后置 |
| M5 war cash | 原生维护/费用来源、实际 producer | 用户要求停研；完成部分冻结 | 实际战争资源同帧互证 |
| M5 multiwar | 共享军队与全 WarID 的资源聚合，复用预留 | 用户要求停研；完成部分冻结 | 实际资源争用与联合选择 |
| M5 family obligation | 婚配最终家系、解除婚约成本、联盟战争义务 | 正在实现 | 新版合法关系与具体义务互证 |
| M5 prewar | 真实绑定参与者、原生集结与未来路线输入 | 用户要求停研；完成部分冻结 | 合格战前场景；未闭合输入保留明确账本 |
| M6 Sway | 活跃实例、好感、最终发送、typed start、终止语义 | 正在实现 | 实例/提交/完成收益与 next/cold |
| M6 law | active/candidate/final terms、费用、已有 LAW8 源操作 | 正在实现 | 有价值的合法法律后置与资源变化 |
| M6 prisoner | 既有囚犯列表、赎金 final terms、typed 操作与独立结果迁移 | 正在实现，14:35追加 | 真实合法赎金、人物与国库后置 |
| M6 Feast | 现有 Stage1/2/5、宾客、Start、hosted/terminal 语义 | 正在实现 | 合格开始、完整生命周期与收益 |
| M7 campaign goal | 普通目标跨 checkpoint/继承保存并驱动下一计划 | static-ready，19+19 fixture GREEN | 自然继承后的实际消费与冷恢复 |
| M7 government | 新版真实 feature profile 与既有封建选择器 | 正在实现 | 实际 runtime 身份适配互证 |

中央 native owner 统一 CMake、bridge、adapter/worker 和 owner mailbox；中央 Python owner 统一私有查询、版本解析及 MCP 接线。目标续接 owner 与 Python owner 按方法块分工。域内原生链继续拆并行子线程；编译使用 64 jobs，每个 build 目录只有一个写者。

## 输入与验收

唯一新 build 输入是冻结 CK3 `1.20.0.2 Crozier / Steam 25588574`，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。实际 provider 必须先有当前原生树与 exact ABI，再进入同一 MCP 和必要生产路径 fixture。共享 candidate/default 构建、源文件及二进制 manifest 由中央收口；不重跑不受影响的已 GREEN 矩阵。

所有运行只使用文件、编译器、mock/fixture；不枚举或查询 CK3 进程，不连接游戏 pipe，不操作游戏、桌面、Steam或当前 profile。全部临时文件、日志与构建在 Z 盘。新私有动作沿既有默认关闭约定，ACK 不能作为结果；不会通过零填 unknown、变更战争意愿或解除 owner/date hold 来造 readiness。

G2 仍 `3/8`，Robert `3153/36524`，新增游戏日为零。宗教/holy order 保持暂缓，婚姻与战争所需最终判定仅使用最小 opaque 输入；其它政府仍保留既有未实现边界。每包在必要验证完成后独立提交并普通 fast-forward 推送，剩余包继续施工。

## 交付与结果

尚无本轮新增完成或 live 结论。域结果在产出后追加具体 commit、测试、artifact、readiness 与未闭合项。外部协调与构建产物入口：`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/`。

14:35追加第13个源码包：现有囚犯列表/赎金旧版native transport尚需1.20绑定，M6明确要求一项囚犯或制度动作，因此并行移植已有ransom路线。旧R0404/5/6 count0保留为当帧真实空场景，不造囚犯或等待自然阳性worker；新包仅迁existing source与消费，不扩刑罚/宗教框架。

### 14:45:01 M7普通campaign目标续接完成

真实driver/service/planner已保存普通 `dynasty_continuity` 意图，沿persisted-v2与既有hot/cold消费者保留稳定campaign ID。fixture中actor100→200通过已有M3 estate核验，继承进度为1，后继实际下一正式计划选当前ruler婚配查询；同目录rogue历史war-first不会覆盖普通目标，rogue原分支仍保持war-first。native_auto_run报告投影同步加入 `campaign_goal_plan_used`，真实service已输出该字段。

新4项与已有succession15项正常模式通过，组合19项 `-O`通过；没有重复已GREEN的全矩阵。结果[artifact](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/campaign-goal/result.json) SHA `e3e59ce40265ee4f68da9714efb800de7dc3b96944dc6c59c0889dc96aae45f1`，测试receipt SHA `1cf9874e42cc28d20f6698c257af09a498882cc0f638441f75e4a1143804ab8a`，初次fixture断言错误保留。源码与边界见[原生输入/消费专题](../ck3-native-ai/ordinary-campaign-goal-continuity.md)。状态仅static-ready；自然继承、游戏checkpoint/new PID、实际家庭结果和后继回合仍需live。其它12包继续后台，不因本包已到live边界停工。

### 14:46:44 M5默认原生集结合法性源码交付

新版默认集结点最终原生合法性已实现：validator `0x298C2C0` → final legality `0x24A48B0`，只构造临时上下文查询，不submit。实际x64 Release `/O2 /W4 /WX`编译和生产路径fixture PASS，三条exact call-chain ABI verifier PASS。专题：[默认集结](../ck3-native-ai/ck3-1.20.0.2-prewar-default-muster.md)；耐久输出 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/prewar/default-muster-wire.json` 与 `prewar/muster-build/build-receipt.json`。状态只为该原生provider的static-ready，公共query route由中央接线；完整future roster/muster/supply与强制参战provider继续并行实现，不把当前合法性冒充未来军力/补给。实际paused互证仍待live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:48:25 M7新版政府真实feature消费源码交付

既有observer/source adapter/binder现已按双版本真实绑定：1.20 campaign/features原生producer→同帧sourceadapter→语义选择器→owned query serializer。新版44项feature实际含by_god_alone而移除barter_troops；旧版44项profile与136项stockflags继续保持，新版18 government rows/171 flags按冻结原版读取。宗教/holy-order身份仅opaque/deferred，其它政府仍为adapter_spec_ready_not_implemented，未外推18政府策略完成。旧3个fixture与实际new44producer在/Od及/O2/W4/WX通过；stock差异增量后只重建新fixture，最终receipt `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/government/stock-profile-final-v2/receipt.json` SHA `f08560ac3eb9155e2e21e079effdfa9abe994c5e0f3dc173021c7b46e5903169`。新版stock verifier18/171及旧sourcecontract4项GREEN；实际C++available/unavailable JSON→driver→官方MCP SDK list/call6项GREEN，Python/中央permit尚另包接回。专题[新版政府适配](../ck3-native-ai/government-runtime-adapter-1.20.0.2.md)。本包native/source消费static-ready，真实paused、封建正式效果、跨ruler/seed/government仍需live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:50:20 M5强制朝贡参战者实际reader交付

现有强制朝贡参战链已移植真实1.20 direct-slot source reader，读取完整ID并保留原生顺序与重复；实际新版land `+0x1C0`、DB `+0xF00`、default `+0x9F28`已落代码。Exact ABI核对6 spans/10 instructions/7 calls/7 RIP/2 literals及RTTI/stock SHA GREEN，MSVC `/Od`与`/O2 /W4 /WX`生产fixture各11 cases通过，真实serializer JSON已解析。耐久结果：`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/prewar/participants/fixture-result.json`、`abi-verification.json`、`Od/forced-participants-wire.json`及`O2/forced-participants-wire.json`。专题[战前强制参与者](../ck3-native-ai/ck3-1.20.0.2-prewar-participants.md)。本包只提升这一来源static-ready，完整宣战参与者、自愿盟友、集结与未来补给不外推完成；其具体producer与中央MCP route仍并行施工，真实paused最终互证待live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:54:45 M5同帧多战争共享资源聚合交付

正式collector已消费同帧全部active WarID的资源聚合；按显式actor/army/resource身份去重，pending/未来费用/政策reserve分开、占用并集保留，只预留已选择的动作即时费。相同actor军费或共享军队不会每WarID重复计算；没有共同期限或真实输入时仍给具体incomplete。wartime诊断保留原selected_step、war owner与date hold，未修改意愿或解锁正式动作。四个受影响模块普通及`-O`各67/67 GREEN，包含两战争共享成本、缺第二战争和collector/dispatcher真实消费；synthetic fixture不作live。耐久manifest `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/war-cash/aggregation/manifest.json` SHA `4e3a557b45f765c6ccc5579d7a03af6394a74b3f82289ff7619d030bb46c92c6`。专题[多战聚合](../ck3-native-ai/m5-multiwar-resource-aggregation-v1.md)。本包聚合层static-ready；实际native现金生产者/来源适配继续施工，当前维护率不会被当作未来上界，完整战争预算与实际资源争用仍未证明。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:56:56 M6法律collection/final terms/typed mutation源码交付

32个已验证域文件已完成：active/candidate collection实际读取、final CanEnact及完整费用/复制reason、owner-thread query wrapper、typed mutation命令。新版actor context+0x1C0、group+0x40、group database数组+0x50/+0x5C、compiled cost+0xC40已映射；命令复用真实clone/lockedqueue bool，未沿用变化后的旧popup提交签名。Collections8 ABI anchors与12 cases在Od/O2 GREEN；terms24 ABI checks与actualcollection→terms→serializer四MSVC cells GREEN；mutation17 spans/24 unwind/12 edges/8 vtable pointers/2 RTTI和typed命令四MSVC cells GREEN。真实wire SHA `2fca001023f181a7a634af9b5c5f140ce986dbbb6128561044f3f318acc68e9e`，实际Python解析1项PASS；初次terms-wire link harness RED保留。耐久证据 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/law/ready-files.json`、`mutation/result.json`及terms/collections各结果。专题[法律集合](../ck3-native-ai/ck3-1.20.0.2-realm-law-collections.md)、[final terms](../ck3-native-ai/ck3-1.20.0.2-realm-law-final-terms.md)、[typed mutation](../ck3-native-ai/ck3-1.20.0.2-realm-law-enact-mutation.md)。这三个来源/命令primitive仅static-ready，完整LAW8 production resource/successor/sourcebinder与独立receipt仍继续施工；global final合法性early-true不会被伪装成已观测的每项CanHave/CanPass。真实有价值的法律与active/resource/successor后置待live，不强制旧CA1。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:38:00 Feast actual-wire Python transport

Feast17文件首包接入 exact-build provenance、实际原生 terminal flags 和现有 pending Start 路径；真实生产 serializer wire5项与受影响既有36项通过。未把Start/ID/debit当作完成；当前尚未包含随后4个实际counter追加。证据：Z:\ck3_mod_rewrite\.task-tmp\g2src\artifacts\g2-offline-2026-10-01\feast-python\transport-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:38:28 Faction actual native source and mailbox

实际完整FactionID、原生power/threshold/discontent/danger、county-only威胁与held-title/vassal-contract递归已迁移；县列表stride18、owner指针及UI比例已按新EXE闭合。Od/O2各7案例及旧reader/serializer测试通过；ABI布局53锚点、metrics22跨度、county10锚点。harness LNK2019首次失败已保留。静态就绪；paused值、SDK实机一致性与gift结果仍待实际验收。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\factions\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:38:48 Gift native final gate, owning command and independent receipt

实际on_accept gift_value费用、玩家付款钱包、final CanSend、原生opinion/modifier、拥有型queue与独立full-generation faction结果已迁移；不是generic on_send零成本。Od/O2 opinion各151断言，slot34四步router各22检查及实际8份wire通过。保留首次harness失败；ACK仅代表提交。自然eligible收礼人、实际扣款/修正及cold结果仍待实机。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\gift\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:38:55 Prisoner collection and actual ransom query/action sources

迁移原生囚犯集合、final赎金terms、拥有型SubmitCommandCopy与独立custody；9种原版选项含current_herd、normal_ransom_cost_value。复用停止战争研究前已完成且赎金必需的release-pair判断，不开展新的战争工作。Od/O2 collection各8案例、ransom各463断言、既有retention各13案例、实际Cpp wire各3份通过。slot53/54不变，纯serializer拆分便于真实wire验收。付款/custody/live/cold仍待验证。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\prisoner\package-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:07 Government actual caller packet and SDK metadata repair

实际Prepare/Submit→原生owner pump→Wait/Reclaim→CommandResult caller补齐accepted/private_build/read_only/advertised四字段，修复确定可复现的SDK BridgeUnavailable。Od/O2实际caller与新增1项SDK通过，既有6项SDK证据复用。首次User32链接harness失败及缺字段包保留。fixture进程没有游戏roots的unavailable只表示测试情形，不冒充live。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\government\caller-final-v2\receipt.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:14 Family lineage preview and betrothal break terms

33个非战争文件实现实际UI子女house预览、父母full House/Dynasty与解约final CanSend/费用/原生条件；不把预览当作出生结果。Od/O2生产wire各4案例和实际SDK6案例通过。另7文件仅归档用户停止战争研究前已验证的联盟历史源，候选未注册战争reader，MCP不提供ally参数，停止继续开发。当前非战争暂停观测、真实解约及cold仍待验收。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\family-obligations\final-source-package.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:20 Sway exact-build state, command and material outcome query

38个owned文件移植实际新manager/storage/full实例ID、进度/目标opinion、最终shown/valid/CanSend、拥有型send和新鲜实例receipt；真实owner-envelope与production source Od/O2通过，四份actual serializer wire进入Python。独立outcome材料观测可用，但hidden阶段history、cancel/invalidate终止原因未实现；ACK、实例出现、100opinion都不冒充phase或terminal。状态static-ready，实机与cold仍待。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\sway\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:27 Religion research resumed and actual current context provider

按用户明确解禁恢复宗教：先落新版stock及原生解析树，再实现真实只读Rite/Faith/Religion/mainRite refs、stable tags、fervor/精神满足度signed Q100000。Character+B4是Rite而不是Faith；实际getter处理原生fallback，保留nil/合法零与读取失败。Od/O2各20检查及实际wire parse通过，PE verifier19函数、25语义指令、14生产常量通过。当前独立library static-ready；中央/MCP/paused查询及通用转换最终判定尚未交付，不涉及战争。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:33 New G2 file candidate and real MCP readonly plan

新候选纯文件工具使用最终40 ON/4 OFF：旧council slot33、warcash/prewar/plannerdiag OFF，新版候选走slot41，LAW enact保留。真实stdio parser验证七项nonwar只读permit，typed action开关不加入只读计划，lifetime无假参数。接口3项测试通过；待中央最终source/binary pins后实际准备全新Z目录和完整匹配save/driver，不把canonical rogue存档称ordinary资格。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:39 Council actual candidates gates and typed assignment runtime

28个native/research/docs文件迁移实际新候选生产、full-ID角色/task解析、四最终gates及拥有型任命helper，slot41五步private transport复用原语义交易与serializer。Od/O2候选各35、gates各25、实际源链各18，32份真实Cpp wire与后续独立receipt通过。保留首stack overflow和缺route宏/链接harness尝试。paused候选/自然negative/任命postcondition/next/cold仍待验证；没有G2 credit。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\council\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:40:45 Government family and prisoner Python actual-wire routes

19个leaf文件绑定新版government/family非战争/prisoner实际wire及exact-build provenance；GOV7、family6、prisoner4及受影响legacy32通过。保留缺字段/quote epoch/旧driver默认签名的真实失败证据及最小修复。family只是UI预览；prisoner集合fixture正向quote为constructed DTO，不冒充final原生getter。共享driver/MCP仍等其它包最终冻结，本包不含战争新入口或live声明。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\python-routes\CORE-READY.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:41:29 Realm law production source, resources and action receipt

续交LAW components/selectedsource/actionmailbox：实际CanHave/CanPass/CanKeep、succession枚举、active法案和真实资源/继承人读取闭合，slot37拥有型命令与独立法律/prestige/full-successor结果。components15 ABI跨度、8property及16enum/literal；Od/O2生产query/action/receipt通过，既有4夹具32案例复用。首次32文件43b262e已交付，本包补齐其余34；不是CA1强制策略。有意义法案选择、真实执行结果和cold仍待实机。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\law\ready-files.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:44:51 Sway and law actual-wire private SDK transport

13个独立transport/test/docs/真实wire文件闭合Sway读取/progress/submit/独立receipt及LAW观测/typed submit/独立receipt，经真实driver和MCP SDK验证21个unique案例与2 receipt subtests。显式law选择/预算，不把ACK当作生效；Sway hidden phase/terminal仍未闭合。实际生产wire的初次harness错误保留。status为static-ready；共享driver/MCP随后独立提交，paused/material/next/cold尚待。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\python-sway-law\READY.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:45:46 Feast full native planner costs guests start and terminal migration

97个native/research/docs/tool文件接入实际1.20 planner1/2/5身份、原生最终CanStart/4费用/guest-arrival、typed Start、完整hosted ID及completion+421/invalidation+422。规则provenance、stage2确认helper和资源leaf闭合；真实prestige/stress/RevelerXP before/after provider→serializer Debug/Release各8案例，公共gold/prestige/piety/stress leaf O2 W4WX4案例通过。重复利用已闭合planner/guest/cost/start测试。消失不代表terminal，counter变化不代表Feast因果收益。状态static-ready，自然Start/扣款/后续terminal/next/cold尚待。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\feast\tracked-source-manifest.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:45:53 Feast durable outcome counter consumer

首17 transport已提交后追加真实4counter nullable解析及现有service.plan_turn defaultOFF durable consumer，不更改选步。实际Cpp native baseline/post→Python新增2案例PASS；consumer改动后15案例联合PASS（12既有+3新增）。旧41/旧MCP2未重复。terminal后首次合法材料观测保留真实空XP而不造零；before/after trace不冒充奖励归因。未获自然Feast live/冷恢复资格。证据：Z:\ck3_mod_rewrite\.task-tmp\g2src\artifacts\g2-offline-2026-10-01\feast-python\counter-append-result.json；Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\feast\lifecycle\outcome-counters-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:49:34 当前精确 source commit 汇总

以下是 shared source 分包 commit；delivery worktree 在每包普通 rebase／FF push 中保留并发上游，master SHA 可与 source SHA 不同。每包 commit/push 完整输出保存在 `artifacts/g2-offline-2026-10-01/*-commit-push.log`，中央最终 manifest 单独绑定实际编译源。一次上游差异核对已确认 `43b262e→8819f0a` 的额外变化是 mod工具／CI依赖／文档，没有 native 或 Python bridge 变化；没有因此重建无关旧矩阵。

| 包 | source commit | 含报告的路径数 |
| --- | --- | --- |
| council | `34ba817861cf0a70445641eb5ba1855886c41099` | 31 |
| factions | `87b419e2cba41de5156dde5aaefb2dfae0a2a31d` | 19 |
| family-obligations | `ba6f383282f46e46cd82521a9cec89ac7f0b358a` | 43 |
| feast-counters | `9bca801817c566bcfafcf1ed6d1bc8b0741fbfdf` | 9 |
| feast-native | `36f7ace8333ea4ad8218ec3b8844197b7f46552f` | 100 |
| feast-python | `442c801222f5f3be07885c29434c455efb933363` | 20 |
| gift | `c3646fad7c610daa0e02db2805c3f3e1fb56478b` | 19 |
| government-caller | `181382bcfffa4a15b6361b06a93117866332241f` | 8 |
| government-native | `16b5dee5397f6342bb6c6976976036d8d07b98fb` | 17 |
| law-native | `43b262eb42246b530c96625eca129e270103c7ef` | 35 |
| law | `b285a6943b87041f2ce81c04836b50a0e7865a1a` | 37 |
| multiwar-aggregation | `5a49a8186b911b4c0f958b96dae3a5f8705c4b98` | 8 |
| prewar-muster | `a4f0407c50ca8b903c41c55cc1253ff0c8a18391` | 9 |
| prewar-participants | `fbc3f93224dcad491c3d394d1b4e1c65e894b170` | 9 |
| prisoner | `081c09d8294b54083612c345275ce15d152a4885` | 30 |
| python-core | `1bb35d65504316cde6ef4b90dd8668b3a6f36531` | 22 |
| religion | `355c7edecc99482b2520106300505235532603b8` | 12 |
| runner | `ff6bb2c7ab2457e292b96ac7780d78f9eae0add1` | 7 |
| sway-law-python | `afafa88d509ef22fe00f78e1d88ff345780f80d9` | 16 |
| sway | `23f336478dc7989e275819f01f4dcb4da77bd60a` | 41 |

当前仍在做最终中央／共享MCP接线与file candidate，随后root唯一实机操作；宗教下一增量独立继续。战争38源冻结，原失败及未验证source边界保留。

### 15:52:28 Ransom required current retention runtime wiring

在已交27文件上最小补齐赎金消费者必需的既有retention来源：slot53 mode／精确step matcher／原DTO／独立querycounter，复用停止战争研究前已闭合provider，未新增战争研究或政策。仅新增生产provider→serializer O2 W4WX3案例（非空／完整空／selector）通过；旧13×2 reader直接复用。完整清单29文件，实际改动单独提交。查询不代表支付／释放；尚无新版实机。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\prisoner\package-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:52:34 Nonwar candidate supervised cold-session plan

更正最新授权scope（宗教允许研究／战争停止），将本轮NEXT从自主lifetime/next改为exact preflight→root监督native-session cold→实际MCP paused读口。真实CLI parser新受影响1案例通过，native-session没有虚构start-paused参数；暂停只能实际snapshot确认并必要时显式pause后再读。不是已launch／已验证binary。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\runner-paused-supervision-argv-plan.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:54:27 Central nonwar runtime dispatcher and current resource snapshot

中央13文件加既有gold getter2文件接入新版本非战争callback、worker permits、拥有型mailbox和实际CMake target；候选40 ON/4 OFF，默认全OFF，冻结warcash/prewar/alliance/religion查询不进入本轮target。实际dispatcher default63/selected186检查通过，注册31callback通过，公共Snapshot实际gold/prestige/piety/stress及负债leaf夹具通过。修正Gift/Sway selector、Council status零revision轮询、Crozier成本与guest provenance installer；不fullread status，不把ACK当结果。gold只复用已完成treasury getter，未继续战争研究。最终双配置DLL/injector64jobs正在收口；source/binary最终pin和paused/live资格另按实际回执。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\central-source-package.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 15:59:19 Council faction and gift actual native SDK contracts

32个leaf/test/真实fixture/docs文件闭合实际议会query→typed assign→后续独立incumbent receipt、实际派系DTO和赠礼preview/提交/独立gold-opinion/faction/cold读取。实际复现并最小修复完整CanSend=false被误判不可用、显式gold reserve被旧10m硬编码覆盖；ordinary默认10m保持。24个unique案例与2 subtests通过（首轮16PASS/6FAIL保留，失败7和受影响旧默认2聚焦通过），不是重跑所有旧矩阵。SDK fake PID和synthetic storage范围明确；自然paused/material/next/newPID资格仍待。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\python-council-gift\handoff-manifest.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:02:35 Final nonwar native driver service and MCP SDK integration

共享native_driver／service／MCP及剩余58非战争清单最终冻结（其中已交leaf无diff），绑定真实GOV／family／prisoner／Council／gift／Sway／law／Feast packet及typed private wrappers；全部正式trial默认OFF，仅显式私有permit可调用。新增赎金必需既有retention实际positive／known-empty wire经SDK1案例（2packet）通过；不抹既有pending／successor承诺。另9文件只保留停止指令前已经验证的历史cash transport依赖，lazy import一致性所需，候选cashflag OFF，未继续研发或复验。真paused／material／next/cold尚待root实机，不以mock SDK完成OODA。证据：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\python-routes\FINAL-SHARED-READY.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:02:42 Distinguish compiled input and final source metadata

runner receipt增加build_source_commit／source_freeze两metadata字段并说明最终source与实际target source pins；不改runtime，不重跑已经通过的接口。最终profile按中央已编译binary和最终已提交源码绑定，metadata freeze不称重新编译或实机。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:06:37 Root SDK paused nonwar sampler

3文件提供root实际SDK readonly sampler，消费真实runner eight-permit argv；canonical ck3_take_snapshot先确认paused actor/date/revision，每域查询前后实际snapshot，原packet/errors留存。未知family/Sway IDs显式skip，Gift只消费真实root count，不造recipient。7个file/fake-MCP测试通过，无启动server／游戏；只有root显式execute-readonly后才能生成实机证据。证据：Z:\ck3_mod_rewrite\.task-tmp\g2src\artifacts\g2-offline-2026-10-01\paused-readonly-sdk-sampler\result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:41:04 Religion current context MCP query

新增default-off ck3_query_player_religion_context_v1和真实Cpp→Driver→官方MCP SDK链，新1案例通过，旧leaf3+11/native41×2复用。19精确文件闭合当前宗教identity/resources查询，不宣称转换资格。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\python-religion-next\SHARED-READY.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:41:37 Religion actual readonly mailbox

真实当前宗教context原生mailbox与complete command_result接通；旧protocol_version缺失的真实SDK RED已修复并保留，Od/O2各41检查6wire通过。新增namedpermit fixture源由中央单次O2收口，不重复旧矩阵。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion\mailbox-delivery.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:42:06 Native state Rite source identity

按实际topliege/primarytitle/stateRite getter读取国教Rite，转换判定复用同一来源，不复制猜测。ABI6func/3regs/23ins/11constants/2stock；Od/O2各14case22checks8wire通过。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-governance\state-rite\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:46:25 Distinct Rite and Faith head identities

分别真实观测actor Rite head、mainRite head、Faith宗教头衔holder，合法vacant/absent区分，不按null猜制度。ABI6func/3regs/14sites、Od/O2各18checks6wire通过。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-rite-governance\head\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:46:32 Native Rite organization counters

读取实际玩家Rite cached county/character follower counts，nil与合法零区分。ABI9 spans/15指令/4constants及Od/O2各13checks4actualwire通过；完整成员collector另包继续，不以计数冒充名单。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-rite-governance\organization\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:46:39 Native chaplain reassignment gates

读取实际玩家chaplain与full-ID候选，真实valid_position/valid_character/CanReassign独立bool，尚非完整typed action资格。ABI8spans5edges，Od/O2各23checks7wire通过；首C4389夹具RED保留。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-governance\clergy\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:46:46 Native Rite conversion final query

实际currentFaith Rite集合、原生paid最终29A34C0判定与full RiteID就绪；不执行转换。ABI25指令spans/最终vtable，Od/O2各14checks9实际JSON通过。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-conversion\rite\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:46:53 Native conversion nonmilitary outcome source tree

9完整原生函数/25语义锚点/2RTTI/14非军事stock windows闭合转换结果源树。Fulfillment非固定delta，首都不会自动免费改，knowledge非直接100%；research/static-confirmed，尚无新结果provider。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-conversion\outcome\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:47:00 Native Sway phase success chance input

实际2A4A400 signed Q100000当前roll百分比、33指令4native spans2虚表7stock就绪。机会周期计数不是成功次数，当前roll输入不是结果；保留首人工位移夹具RED，终止和history provider继续。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\sway\completion-phase\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:47:06 Nonwar event sources and combined stress consumer

六事件冻结新版源码与直接依赖，实际stress_and_fulfillment使1190/5007生产policy阻断已确定性复现并最小修复primary stress两分支，未把fulfillment当效用。10 passed/5 subtests及首RED保留。major stress新旧均-65，旧-80文案纠正并按既有生成器刷新。旧治疗modifier/县材料观测ABI仍待独立新provider，未假报完整live。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\events12002\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 16:47:13 Native Rite conversion piety quote

真实dynamic int32 native piety报价与paid最终命令distinct，quote available不代表affordable/allowed。ABI6complete functions/5slices/38anchors6bindings及Od/O2各9场景14checks5wire通过；复用Rite包command结构。 状态与边界以manifest为准，本包后台完成，无CK操作。清单：Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-conversion\cost\delivery-result.json

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。
