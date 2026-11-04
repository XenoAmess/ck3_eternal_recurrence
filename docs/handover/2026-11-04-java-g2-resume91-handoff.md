# Java / G2 resume91 交接（2026-11-04）

现场时间统一为 UTC；本地时区 Asia/Shanghai。机器：`xenoamess-full-tower-eb9d2c1186`。本文与 [来源索引](2026-11-04-java-g2-resume91-handoff-source-index.json) 配套阅读。

这是用户要求的文档交接，不是目标完成，也没有把此前“继续执行”改写成休假授权。本次只读取既有原件，没有为写文档新增游戏动作、保存、GET、采样、编测、部署或进程停启。当前委托是在交接前自然失败；不能把旧 LOOP 当作当前仍在游玩。

## 接手先做什么

1. 先读索引 `runtime_thin`、`runtime_summary`，核对最新 OWNER、HEAD、原第117批报告与邮箱请求 custody。当前是 **FAILED_DELEGATE**，不能按旧105/108或23:09的 LOOP 直接续发控制。
2. 原第116批父动作2218已经 APPLIED，C62已结算；不重 ARM、resume 或原父动作。第117批 fallback 在写入前拒绝、发送0字节；先解决原邮箱请求的真实终态/归属，不覆盖邮箱、清账本、刷新原期限或盲发 fresh READ。
3. 保留同一 CK3 局。Runtime 独占 Game、Native live、委托、S/MB、账本、GET和装载；Native负责必要离线执行及资源；Java负责正式Git；Models负责共享模型运营。原岗位名是归属导航，不是活跃证明。已完成或闲置岗要用 `followup_task` 真正启动；`send_message` 仅送信。
4. P0仍是正常游玩及功能/性能。先闭117实际阻塞，再推进已有精确性能候选；模型、Git、G2研究不成为同局恢复的全批前置。不重跑旧绿色检查，不为文档或背景候选增加恢复成本。
5. 接入本地模型前同步父目录独立仓库，按下文恢复唯一滚动入口；先核实际进程与去重账本，不能根据旧启动回执再开第二套。

## 当前运行切点

主依据为运行岗在 **2026-11-04 02:38:06.862682 UTC** 冻结的 `handoff-readonly-20261104T0236/THIN.json`；完整 SUMMARY 保存各原件引用。Root已逐行读取该薄件。它不是新的 Game/Win32 现场查询。

| 项目 | 可核实状态 |
| --- | --- |
| 当前局身份依据 | Game77132 / birth FILETIME `134380410301009189`；来自原账本和最新原观察，本次未新查Game |
| Java宿主 | PID76092 / birth `134381592437332478`；OWNER原观察为exit259，不代表业务委托健康 |
| 最后委托 | `f6e15a21-ab3c-4960-afa1-5596a274c636`，restart8；02:28:31.150875300自然 `DELEGATE_COMPLETED` / exit4 |
| 旧LOOP | 2026-11-03 23:09:08.114934；该次冷恢复2160.346300900秒，仅历史 |
| 最新HEAD | 2225 / `BATCH_DEFERRED117`；C62 / pending=null |
| 最新结算帧 | 02:24:47.523601700，date_raw53156760 / native1291 / public1189 |
| 本局进展 | 449日已结算，365日已确认保存，84日未保存；origin_raw53145984 |
| 第116批 | `WALL_TIMEOUT`，1813.695589500秒，1attempt / 1APPLIED / 0SAVE；父2218已APPLIED |
| 第117批 | `OBSERVATION_UNAVAILABLE`，14.879548700秒，0attempt；原mailbox attempt unresolved，fallback `BEFORE_WRITE` / 0bytes |

第117批 fallback 是 `fresh-state-e4a834b48d7c4e6e8043fb74fe8c5ae4`。它的0字节不表示可以覆盖另一原请求的 custody。当前没有新world UNKNOWN，不等于全历史 UNKNOWN 已清空；原108的只读恢复2067/2068/C57等证据仍在完整 SUMMARY 中。

旧监护77093只冻结到02:23:14；本次工具返回 Unknown process id，不能宣称它仍运行，也不能据此补写自然退出。MODE中的历史 active/LOOP 字段不是当前健康权威。Native原资源账本最后三槽为null，Main301段属于历史，不能用它推断当前Runtime。

### 保存与性能口径

用户已明确改为**每年保存一次**。普通自动SAVE按最后已确认savedPair的游戏日期差达到8760 raw（365日），并保留原SAFE、显式保存、首baseline及UNKNOWN约束；不再按每Life/每日/批数保存。当前 saved date53154744，与最新结算相差2016 raw / 84日，年度门未到；不要为交接补SAVE。

10秒/游戏日目标仍未达到。主指标是明确窗口内端到端墙钟 / 新增 `SAVE_CONFIRMED` 游戏日，包含准备、等待、失败、恢复、冷启动；零新增保存日报告实耗和零保存，不报有限秒/日。Observed、周期结算、child推进与保存分别记。当前116/117窗口均0SAVE，不能拿累计365作这两个窗口的分母。

## 已发布的关键修复与采用边界

| 提交 | 交付与验证范围 |
| --- | --- |
| `60fffd5357` | 年度自动保存策略；原9项验证，不是每一保存/继承场景都已实机通过 |
| `79ef57db99` + `0f4608b112` | AdvanceClock Status传原parent deadline，Native单RPC仍60秒；2新测试。104实际Status36.532206秒后超原parent期限2.0753767秒，证明新期限已传入，不是旧60秒整包错误 |
| `5146304b65` | 年存dirty/已有settled工作不再绕过新Life预算；Loop按最后返回PLANNING识别未派发动作，并保真正连续二次无进展停止。首780=2P7F；夹具接对三参数planningUntil后781只重验失败7项，合9个不同PASS |
| `263b478307` | finalizedMarker只做facts DATA检查，避免无谓full projection；2生产叶、3新测试通过 |
| `39a06d1fdb` + `42d8d2a6b7` | Persistent私有回放减少重复图守卫与公开手工见证；具体运行variant和热载正例见下节，不能只凭formal宣称当前组合/速度通过 |
| `03795d0059` / `2f6cb139c4` / `94ac3e9116` | historical read scope、借用活跃scope和退出后恢复写入；strict/局部3P/新2JUnit分层保留，不授完整Root issuer链或任意组合 |
| `53ec1d5897` / `2e16b7cad4` | Journal、Collector的窄重复工作优化；实际variant与输入fixture资格独立于formal whole记录 |
| `4af48c28b2` | Known构造保守兼容修复，恢复新鲜的晚期比较；明确0fast / 0性能信用 |

截至文档准备，正式业务工作副本 `D:/r64d` 的 HEAD为 `11aaa557101bbb0fb43b0f78bc3ad52af1edb06e`，干净。文档提交会产生后继HEAD，不能把这个源码切点写成文档发布后的HEAD。

### Quarkus和当前P0

默认运行方式为 Quarkus dev，不回到旧plain Main模板。正常同JVM loader重建、同局恢复与保存已有真实通过；结构/API变更与仅方法体修改必须分开处理。

已有 Persistent783 R2 的官方instrumentation/noRestart正例：约3.120秒，同250f77/restart7、无新delegate。不能泛写“原地重定义从未成功”。它也不证明新四hook harness、任意类型/结构改动、agent artifact闭包或多叶原子采用全部通过；具体索引以后见原件为准。

783单次真实线程把冷恢复定位到 `snapshotProjectionSafe → cooldownSnapshot → replay → Journal.retain → sameGameHistory → BOOT`。后继已有重复守卫修复与817/836两次30秒JFR；它们均已自然闭合，不再重采。样本数、CPU lifetime、GC事件不能当完整阶段占比或唯一根因。

当前另有109 upper候选只有872 strict，installedSource / strict历史支路 / fullRoot fixture仍GAP，不可把它并入当前装载。新四hook instrumentation harness的source及19项具名输入已齐，但依赖实际获取、Dev-agent选择/classifier仍NOT_HELD；`TRUSTED-ACQUISITION-PLAN02.json`只覆盖install-plugin3.2.0 help/pluginrealm，不等实际获取或harness通过。

## 八M及相关源码队列

最后完整G2验收仍 **6/8**。M6/M7的自然多场景、继承/活动等验收没有被源码量、软件PASS、普通Life或模型次数代替。下表的“未持”是该交接边界缺回执，不能擅写成全球从未执行。

| 线 | 当前交付、未闭项与接手动作 |
| --- | --- |
| M0 / P0 | Persistent783有801首编、802受影响2项及808新2项通过，正式39a06d1f/42d8d2a6，actual源99dd已instrumentation采用；未证提速。Known保守修、Facts旧Set优化ff2f01ca/5P与新wire fa057不可混；新wire/GUI只持SourceReady。759两模型源审均拒，未选择公共descriptor快路；109 upper872未采用，Publisher双Source-null路由与Root-owned OrBorrow/issuer合同仍待闭 |
| M1 | 维持最后完整验收等级；旧parser/hash-collision研究遭guard的主题不重开、不转派。不要根据旧owner名恢复同题。新工作必须是独立明确的业务缺口 |
| M2 | 662当前主未闭：Native876已补103B原件，模型生产/Exercise源拒，guided R2截断整弃；owner生产/483L Exercise与literal尚需整体审和首编。659成熟四场景的新thin wrapper只source就绪；665未持首编；661/664有strict、RUN未持。660保870首红，891 literal修后903同场景绿；663保BOM红，879/893绿，成熟包已Java、正式回执未持 |
| M3 | 309/310和311已正式 `f5d3ded2be`；312/317已正式 `012a54a751` / `88c7330047`。314仅strict；315/316源码齐未持first；318/319源码已完成只需必要first，勿再派作者。313/320遭guard冻结。321仍缺855F00完整ASM/末界/内部CALL及SP/DF/FP，不能拿40L scalar升级full-frame producer |
| M4 / 显示 | 窗口fit正式 `6cb3869ab9`、11DATA，并有23:04实际同Game适配2560×1440→2560×1392及HUD完整回执；只授当次caller awareness0/96DPI坐标域，不泛化其它屏幕。窗口消息835仅3DATA。最终视频current-v1有实际画面验收，R2代际路由仍是另一个未成熟候选 |
| M5 / JSON | typed130/131有5软件PASS但旧异常processor codec语义改变，formal暂停。后继136/137/138保公开null-codec与旧cursor codec两合同；825已有coherent两TU首0/7class，已编117受影响一方法RUN-only1P、新137首1P，合2P；formal仍暂停，新增类型加载未知，不能借旧131四绿。Strict114默认3P后因合法InputDecorator观察差异源码拒收，未采用；UTC `6a411c0058`已正式，Assembler仅Test `ac0615a80b`正式，不能挪用standalone生产3P给formal组合。Decimal124/sorted123源码就绪、first回执未持 |
| M6 | wholeActivity266正式 `3dbc4e87b3`，原3场景；Guard264 `68ad2b4e37`、Word265 `8e372149eb`、GenericChild259 `d615775249`各有限软件资格。Dynamic235正式 `62a1b91db8`但无Runtime采用回执；270仅current对照。自然nomination/三cap安装/assessment仍NOT_HELD。277两prod→两新Test→两scene、278强recorder首次RUN是具体后继。23FC7E0只48B，下一具名32B `[23FC810,23FC830)`尚未取，禁止猜tail/全PE邻扫 |
| M7 | 普通Saved路由 `634fd6ee`、继承Inputs `7d73b0bc`、signed/seed `029df72b`、NEXT deadline `7b3f8852`、safe-stop `af72ffa6`均组件级；不授私Managed、自然NEXT/继承全场景。BATCH77只实际消费dynasty/marriage等既有字段，未有完整gov/context/source_epoch/executable_ref。instrumentation四hook资格按上节继续 |

显示/录像最新已发表另有 `11aaa55710`：只把源码预备码率4800改4400以留managed profile余量，0新OBS/录像或实际prepare。该源码尚未替换Runtime package01的旧4800配置。

最终视频是**独立实际结果**：`final-video-current-v1-runtime-preparation/FINAL-VIDEO-ACCEPTANCE02.json`，14.566秒MKV、平均4337136bps；Runtime实际查看7s/12s帧，Game+current Java-v1白字/黑60%/无边框，没有桌面决策窗。最初5001096bps超5Mb上限的RED保留，后继只对已关闭媒体离线4.4Mb重编码，无新OBS采集。不能授持续录像/EDL健康、新SAVE或R2代际路由通过。

R2 `RootDecisionDisplay`及新Test02仅构造/关闭未render对象的两个DATA方法SourceReady，本交接未持首验/正式/Runtime采用；typed-card、claimed generation、late-old-render、跨loader仍是具体缺口。当前实际feed仍v1，不能把R2候选当现用。

## 模型与并发的长期运营

- 共享仓库：[local-model-operations](https://github.com/XenoAmess/local-model-operations)。本机 `Z:/workspace/local-model-operations`；其它机器在消费项目父目录克隆。干净main先fetch及ff-only同步；有本地改动/分叉保留并按该仓库协作规则处理，禁止reset/force覆盖。
- 先读共享AGENTS、`docs/usage.md`、`config/executor.json`和`prompts/capability-operations.md`；CK3副本 `docs/local-model-executor-config.json`需显式审阅投影，拉取共享仓库不自动替换活跃caller/Game配置。
- 唯一服务 `http://192.168.1.11:8080/v1`，`qwen38-coder`，无密钥，LAN默认DIRECT/不继承环境代理；不回退旧IP/8000。每日OpenCode检查和实际版本复用按共享规范，不能把维护重试变成游戏动作重试。
- HTTP固定三消息完整当前源码；OpenCode原生assistant/tool另记，不硬套三消息。每响应有限输出；用户取消硬12步，不能偷恢复总步数限制。仍检查真实重复读取/无信息循环，记实际owner准备、审阅、修正和验证成本。
- HTTP与OpenCode能力边界持续维护两份记录；不能以试点结束停运营。stop、编译、软件、formal、装载、游戏行为、SAVE分级；length/半截流整弃，瞬时网络错误按配置最多6次，只重发模型请求。
- 云端型号保持当前型号，容量错误原任务重试；当前没有已知capacity待重试，不能把不足60全部归模型容量。恢复idle/errored需followup而非只send。Guard拒绝与capacity区分，不改词、换岗或夹入其它任务间接完成被拒主题。
- 60个实际云端worker与60真实在途HTTP是两个目标；历史有过云端单点60，不是持续达标。最新已持完整工具view为02:23:18、selected65中的13 RUNNING/52 COMPLETED，不当02:40后的实时人数；文档读取岗也不能充作新业务并发成果。当前known capacity pending=0，未达60不能归因容量。
- 最新owned source登记cut：02:40:18，202 POST / 202 END / 0未配对；只此登记范围，不代表global/direct/Runtime/backend。current READY104行/63954B，只余1582B；INTAKE180票/174logical、180receipt、未登记0。历史6次metadata准备错误保留，不冒模型或服务错。
- 旧source intake/dispatcher session99035/56153已Unknown process id；本次具名PID/命令筛选未检出对应进程。不要按旧launch宣称仍活跃或对旧PID盲kill。后继先核唯一owner/实际进程与同DB终态去重，再按共享受控方案恢复滚动；无需要时不重POST终态任务。
- READY已完成一次98行换代，历史两DB/tombstones/outputs保留，换的是READY文件不是清DB。当前又近64KiB，应先按已验只读分类/保留carry和跨代task/output去重处理，不按年龄强杀/清claim。
- 输入规范曾使4项源齐任务滞留约421秒：直接drop把`transfer_evidence`写成dict，legacy registrar要求非空str。candidate03原来就有提前校验，不存在“publisher03放行”修复；该错误归因已撤回。后继优先已审`--publish-only`而非裸drop。

可选registry入口已正式 `d1e2300a`：`call_with_registry.py` + registry模块；canonical `call.py`和活跃兼容caller并未因该发表自动迁移。新bounded registry snapshot CLI的OpenCode任务仍按最新Models原件接手，不能重跑旧三任务或旧M2 session。原试点三任务都有owner纠错，尚未证明降低总owner成本。

02:42:43共享checkout已在干净main正常ff至 `be99677cd393dd2b46c565513eaa049c9206faba`；新增仅其它项目文档，caller/config没切。当前source profile为DIRECT、600秒read/2400秒total/最多6次瞬错；共享executor默认180/900另属一层，不混为实际source请求参数。`call.py`原pin0fdf、pool e1f593、source-high profile97fb38保持；消费项目切换须显式审。

OpenCode版本只按当天已有缓存：1.19.5，检查时间本地00:28:01.979872；文档期未运行版本命令或服务探测。当前没有未闭native pilot；最后lower-counter为13POST/13END、12tool+1stop，CLI45.59575秒，owner三项blocker全拒、0finding。上述bounded snapshot CLI仍是未闭源码提议，不是一个已启动试点。云端保持型号/正确唤醒规则已正式 `5bc648c3`，在长期运营prompt中。

M2 662的三份标准actual-wire审计文件在Models本次核实时未存在，只索原owner现成小ref；不能用prePOST准备审计替代实际wire参数核查。各角色的真实BEGIN/END与终态已有独立记录。

已有DATA调度计划工具不是自动执行器：private796的10项+历史CLI通过；portable源 `0469e484`、后见证据 `e828ae9a`。输入仍是人工保存的实际roster，计划不等协作调用或真实START。缺owner/guard题不能猜重派。

## 文件、执行与Git

| 位置 | 用途/边界 |
| --- | --- |
| `Z:/ck3_mod_rewrite` | 共享workspace，大量历史dirty；本轮观察ahead2/behind1859。不reset/stash/广stage/覆盖 |
| `D:/r64d` | 当前正常master正式发布checkout；Java唯一stage/commit/push，单主线，按明确文件及时发布 |
| `C:/ck3-state/resume91-root/quarkus-dev307/source307` / `build307` | 活跃运行源码/输出，仅Runtime改；不因formal发表覆盖整树 |
| `D:/ck3-state/ck3-java-resume91-business268` | continuity/state原账本；不清UNKNOWN、伪造回执或回滚旧head |
| `D:/ck3-state/resume91-native-integration` | sole必要编验/资源/工具记录；checkpoint904是软件阶段汇总，不是Game验收 |
| `D:/ck3-state/resume91-m0-native` 至各M专属根 | owner候选/原件；详细路径看索引，不把机器路径强加给别机 |
| `D:/ck3-state/resume91-root` | Root审查、精确来源、模型滚动材料及待资格工具 |

执行默认 `cmd.exe`、`login:false`。源码、JSON、`.py`、`.js.txt`都是数据参数，严禁裸路径当命令。读取用已审 `D:/ck3-state/resume91-root/read-lines.cmd`；Python用明确解释器加 `-B -X utf8`和脚本路径，不用shell拼接/隐式文件关联。已有bare-data误执行副作用仍UNKNOWN，不能为60补位重新唤醒撤权actor。

每phase fresh核实际资源和Runtime/SAVE边界，独占输出；两轻窗曾实际重叠，但不是未来并发许可。不要把timestamp TTL当child已退出或清slot依据。831/904等检查、工具首验和当前进程分别核。闭合任务只做下一真实未完成单元，不重复旧绿。

存储不为交接做全盘扫描或清理；沿既有期限策略保当前state、117最小原件及唯一未闭候选，不把旧批量产物自动续为永久保护。

本次只stage并发布本文件与来源索引；不修改AGENTS、不带入历史dirty或背景源码。索引的机器路径/哈希仅作导航，不是启动、恢复或全依赖来源审计的新前置。原始HTTP、JFR、游戏材料、私有oracle数值保留执行机器，不提交到Git。

## 保留的未通过和不要误用的结论

- 年度budget早期R2有同日真实进展后仍误判连续停止的反例，已被R3修复；该R2从未运行采用。不要把它与Persistent优化后继的“R2 / 99dd”混为同一候选。
- 原780夹具7F、660原870语义红、663原871 BOM红及后继修复分账；后见PASS不回写首轮。
- typed130虽5P，兼容性仍拒；Strict114虽3P，源码反例成立；软件绿色不自动授权采用。
- M3 313/320、M5旧encode、旧M1 hash-collision/parser和M2旧654等guard主题保留原件，不改述/转派绕过。未持精确拒绝原因/UTC时写UNKNOWN，不编造。
- 旧resume90“休假停止”、旧Game71464和旧69日等只作历史，不覆盖本轮Game77132/449日的新切点；本次用户只要求交接文档，未授权为文档触发额外现场操作。
