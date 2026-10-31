# resume91 本地模型真实调用与能力边界

machine_id: `xenoamess-full-tower-eb9d2c1186`。源码模型 HTTP 唯一协调为 `/root/models91`；运行期决策 HTTP 由 `/root/runtime91` 独占并预留至少一个请求位。用户本次明确续行并要求高并发使用本地模型，旧休假 STOP 只作历史保存，未改写旧队列或原件。

本轮可复用经验已归入既有[可行性记录](../local-model-executor-feasibility-2026-10-28.md#2026-10-31-resume91高并发真实采用与审阅成本)与[能力边界记录](../local-model-capability-boundary-2026-10-28.md#2026-10-31-resume91方法与整图候选的实际对照)，并与此页互链。两全局文件只追加有原件的本轮结论，owner审阅勘误、schema冲突与真实模型错误分别归因。

采用 `docs/local-model-executor-config.json` 的 `8080/qwen38-coder`、固定三消息源码前缀、temperature0、thinking=false、有限 max_tokens、SSE 有效内容 TTFT/headers/总耗时/usage 分记；cached 字段未报告时保持未知。复用旧 call90.py 的维护副本 `D:/ck3-state/model-dispatch91/call91.py`，未新增调度服务。每一实际请求的完整 body 为各任务目录 `REQUEST.json`，变化任务真实位于最后消息；不是仅 POST 路径或 manifest。

## 19:06:52Z 后继观察与审阅勘误

`2026-10-30T19:06:52.777474+00:00`：97个真实任务/121次HTTP尝试均已传输终态，82个stop/完整JSON、15个length截断；客户端峰值25，发生于18:58:27.389244Z。第三批24次首流ConnectionReset10054分别保留partial并按配置退避到第2尝试，不把接口中断计推理失败。该刻服务running0/waiting0；随后立即滚动派4个仍未闭的小任务（M6 helper/core-test、M0并发source review、M3 numeric oracle），不是固定配额补位。

完整逐项审阅/归因持续写 [REVIEWS91.json](D:/ck3-state/model-dispatch91/REVIEWS91.json)。新增真实结果：M1 Context02原样guard及QueryFailure fixture在D采用、owner补反控后28P；liege17第二轮原样header strictCL0/原118B8分支通过；Surrender新方法原样严格编译0/新3参数3P；M7 special三Java raw-return方法原样严格编译0/36断言，解释metadata仍拒绝；M3 succession返工73行callback原样语义采用，owner提供映射/main后原184B2case/26检查通过。以上都是D软件范围，不能外推生产部署或Game行为。

runtime-install104完整模型候选16.634s返回：factor activeGame与catalog末尾替换被接受；owner另修factory入口和helper可见性。2叶strictjavac0/6.911s，既有PhaseDeadline4P；S/Z采用由runtime记录，慢catalog真实正向留105，不把现成4P称实机通过。初次已发请求没有后来补到的Configuration整类，这个输入事实保留；owner后续结合其operationTimeout合同审阅，无需追认补发。

审阅成本与勘误必须保留：

- M2 random-Java首轮及Java JSON纠正包的字符串曾被owner误读外层JSON转义。真实提取源码核对后撤回该缺陷；M2第二轮因此逐字无diff，虽有真实HTTP也不是新修复。M2随后实际javac44/45字符字面量失败才是另一真实返工03。Court CASE的转义缺陷同样已撤回，其余确切拒绝仍保留。
- Java material所用Binding/FrameLoader/Original getters/settled都真实存在，owner先前API发明分类已撤回。最终未编源审为INCOMPLETE_AUTHORITY_EVIDENCE：authority/journal、实际catalog/action/replay对象同一性及证据/producer closure不完整，原样0采用。不能将该项计不存在API失败。
- 协调岗将hashJava任务后再接含另一Return schema的完整诊断，造成最终输出要求冲突；缺Java源码归封包错误，不能计Java编译失败。旧REQUEST保留；Java02整份替换末消息为唯一candidate_java schema，后续length及实际错误独立评审。
- M2 GUI02稳定源缺少首轮已接受新selector正文，只给了响应路径而模型无文件工具；这是上下文设计缺口，不能据此判单语句能力上限。owner已接管，不事后重发追认。
- 旧模型pair132本轮原样Java对原71B native12270例/0差异，接受D raw predicate但拒绝其几何命名；它属于resume90旧候选的本轮验证，不加到resume91 POST数。

多个完整ASM/全图装配候选出现重复imports/正文直至length、ABI/指针和返回值错误。已在具体链重复失败后交owner接管，模型继续承担有完整声明的小方法/纯数值/实际诊断；不对已完成分析做第三次复述，也不将单项失败定为永久能力上限。静态拒绝与真实编译失败分别记录。部分较早exec session后继poll返回Unknown process id，工具OS退出码不可得，保UNKNOWN，不由HTTP SUMMARY反推exit0/1。

## 真实并发与传输观察

`2026-10-30T18:54:37.666637+00:00` 观察已实际启动 **42 个任务、42 次 HTTP 尝试**；18 个终态中12个 stop/完整 SSE/可解析 JSON、6个 length 截断。当前客户端在途24，客户端区间峰值24发生于18:53:53.998501Z。此数按本机 POST_BEGIN 至 ATTEMPT_END 区间计算，包含网络/服务等待，不能当作服务端推理数。

同次 `/metrics` 实际报告 running24、waiting0、KV57.58%；这是独立服务指标。D盘余577.23GiB、可用物理内存20.18GiB、commit余65.27GiB。运行预留保持；后续按真实服务队列、终态、错误与真实待办滚动，不设每岗调用配额。

持续机器索引：[STATUS91.json](D:/ck3-state/model-dispatch91/STATUS91.json)、[BATCH01-JOBS.json](D:/ck3-state/model-dispatch91/BATCH01-JOBS.json)、[BATCH02-JOBS.json](D:/ck3-state/model-dispatch91/BATCH02-JOBS.json)、[封包读回](D:/ck3-state/model-dispatch91/packets/PACKET-ASSEMBLY-READBACK01.json)。BATCH 是已封包清单，含未 POST/后取消意图；真实调用数仅取 EVENTS。每任务保留 REQUEST、原始 SSE、逐尝试 CONTENT/RESULT、SUMMARY；HTTP200或完整JSON均不授采用信用。

## 已收到的真实审阅与采用

| 任务 | 传输与实际审阅 | 编测/采用边界 |
| --- | --- | --- |
| runtime-sem103 | 首轮完整，headers14.445s/TTFT14.446s/总25.645s；完整SEM误用LEDGER小预算的两行typed parser/reference修复 | owner严格javac0；真实canonical102完整readSettledSameGame、529451B SEM实际transport与错Game guard 2P0F；S/Z采用，MB由runtime增编。模型源码候选不是运行期决策。 |
| runtime-obligations-source | 首轮完整且编译0，但真实测试仍0P1F：raw SHA目标正确，大小写仍错 | owner补equalsIgnoreCase后1P0F；记MODEL_ASSISTED_OWNER_CORRECTED，不能记原样通过。接管时二轮尚未POST，已取消，不计模型调用。 |
| m3-converter120 | 首轮完整，owner原样采用D方法 | 单TU compile0/run0，20 scenes、363总Check=263基础设施+100业务语义；没有Game信用。 |
| m3-filter119 | 两轮完整候选仍含布局/数组拷贝/快照别名/未初始化错误，整候选拒绝 | owner重写unsafe fixture后29 scenes、1210总Check=931基础设施/fixture+279原生语义。模型13case表可留，不能将owner绿追认为完整候选采用。 |
| m1-native-liege17 | 首轮完整；实际CL exit2/C2679：119B赋118B数组，且假造输入文件名 | 未采用；已提供真实编译诊断窄纠错。 |
| m1-context-consumer | 首轮完整但4处捏造canonical API且byte[].equals身份比较 | 实际javac失败；第二轮按真实API窄纠错。 |
| m0-queue-build-plan | 首轮完整但12 objects漏query mailbox、坏hunk抄未改C++且漏main接线 | 源审拒绝，未编测；第二轮要求四段完整小字符串而不输出整fixture。 |
| m0-core-wrapper | 首轮完整但重复allocator、违规改Mapping、fallback pair宽度/offset错误和硬写未测计数 | 源审拒绝，未编跑；保留实际同前缀纠正请求。 |
| m3-bank31 / m3-succession | 首轮分别5000/7000 length截断；另含明确ABI/dataflow与巨大重复布局错误 | 不拼接partial、不自动重试length；分别收窄五字段与<=100行回调/State返工。 |
| M5四业务体 | 12FAD50完整但callee/alias错误拒绝；其余3项6000 length | owner缩短为target stores/args数组的1500–2400预算新任务；输出控制失败与语义错误分记。 |
| M7 preload/special | preload6500 length且条件/参数错误；special完整但寄存器/返回分支错误 | 原候选均拒绝；新轮分别限五路径表与纯Java返回合同。 |

主要采用原件：[SEM103 SUMMARY](D:/ck3-state/resume91-runtime/sem103-regression/SUMMARY.json)、[Family DELIVERY](D:/ck3-state/resume91-runtime/obligations/DELIVERY.json)、[M3 religious RESULT91](D:/ck3-state/resume91-m3-native/religious91/RESULT91.json)。其它原始响应和审阅留各D独占目录；未报告的状态保持未确认，不把静默当采用。

## 本轮探索边界

当前以真实新任务并行测试：小方法修复、实际编译诊断纠错、纯数值ASM重现、单TU typed fixture、多文件consumer合同及同World HELLO/fullSnapshot装配。提供输入大小仅说明上下文，不等于实际改写规模。完整ASM ABI/内存布局重建仍由owner主导；模型负责独立可核的小段，较大候选隔离验收，不阻塞同Game接续。

尚未POST的worker launcher维护在runtime owner接管采用后取消，不能追认模型实现；已人工完成Ranking亦未重发。源码候选与运行期qwen selector分开计数，本岗没有Game动作或运行期决策HTTP。


### 用户更新模型 IP：192.168.1.11 的实际首请求

用户于 2026-10-31 本地日期两次指定新 IP 并要求记入运营；Root 已改唯一配置与 AGENTS。后续源码 HTTP 从配置读 `http://192.168.1.11:8080/v1` / `qwen38-coder`，不继续旧1.7重试、不回8000。旧 command106 五次503+一次reset保留原接口失败归属；未POST的 archive107 在 owner 完成后取消，不补调用。

新地址首真实 P0 `runtime-storage-hotpath108`：UTC20:17:28.587641→20:17:38.031662，HTTP200stop/SSE DONE/JSON，headers3.612s、TTFT3.614s、总9.444s，25828in955out、cached未知、实际OSexit0。四完整源117152字符，末任务仅普通storage两方法；未授编测/采用/加速/Game信用。候选结束即直交Java writer，首答root-loop编辑可用但漏lock-path重复stat，owner已交窄纠错，未将漏项当接口失败。原件 `D:/ck3-state/model-dispatch91/runtime-storage-hotpath108/`；迁移receipt为同根 `NEW-IP-MIGRATION91.json`，call91事件自此显式记录base_url。

此后新IP真实候选按到达独立派发：M5三叶只保留Unavailable/IOException原因，Storage第二方法纠错与M6自然START单方法曾并发，canonical108只删两个纯本地查询的旧deadline guard；各终态已立即直交原owner。运行期HTTP仍归runtime，本岗不调用Game。新地址首成功不是长期服务稳定性或模型能力上限结论，正式经验反链：[可行性](../local-model-executor-feasibility-2026-10-28.md)、[能力边界](../local-model-capability-boundary-2026-10-28.md)。

Storage后继最终回执：第二轮8.943秒/481out，root/lock两hunk分别原语义采入，owner生产语义改0；三源strict0/3.664秒。首跑7P1F、owner修测试清理后仅失败1P/2.185秒，非同JVM8P。Runtime S/Z及正式FF `2377f74ccf` 分记；未授量化提速，MB109 loop/新增日另记。


### 直接派发运营与规模递进（20:37Z冻结观察）

用户再次要求加大力度后，Root已授权八M/Java/runtime源码owner独占taskid直接调用现有 `D:/ck3-state/model-dispatch91/call91.py`，models91继续统一配置/归总，results91即时交付；不再等中央逐包封审或ACK。不新增平台，不重复绿任务。调用器统一读取1.11/固定system/model/defaults；已有EVENTS目录拒重复，支持三消息body或现成source_files/task_path有限spec。运行决策仍runtime独占。

UTC20:37:22.912新IP实际客户端峰8@20:36:59.164561、在途4，有限metrics running4/waiting0/KV原值0.1489899；20:37:31稍后快照39任务/41BEGIN39END、在途2。旧IP峰25不计新IP；24–32目标未达到，运行预留一位只是调度意图。29源闭包105690in6500out虽200但length，81.093秒；Focus95820in1698out完整54.942秒；ledger13源55611in3259out完整66.547秒但源审拒；NamedValue完整候选6249out/92.104秒仍源审拒未编。保真实大任务探索，不把输入规模写成改写规模或把完整输出当采用。

canonical108原样两edit实际必要1P并正式FF `9f9728ecc7`，Storage两轮各一生产hunk原语义、owner生产改0，三源strict0、首7P1F后owner清理修正仅失败项1P，FF `2377f74ccf`，无加速/新增日推断。ledger纠错POST后Root取消fullproof重复审计，晚到scope另记。新IP首运营三append/config观察已正式FF `b1acb0d826`，旧观察保history；本节及两全局经验只EOF新增，不覆盖正式旧字节。


后继 Army cohort04：52源/116097prompt4330out完整stop82.321秒，owner将12真undefined生产者/14obj模板配置物化D，实际编/链0，仍待验证，不授生产/Game。新服务实际接受120427总tokens，窗口声明上限仍未知。


### resume91 真实未解诊断的 thinking 请求观察

Root 明确授权在仍未解的M5端到端诊断上做一次单请求模式探索：`m5-end-to-end110-correct` 与 `m5-end-to-end110-thinking` 的实际三条messages逐条完全相等（稳定源475409字符、末诊断54267字符），只有 `enable_thinking=false/true` 与 `max_tokens=10000/16000` 不同；全局默认false未改。两者均真实HTTP200/stop/SSE完整、调用器实际OS0：前者113262prompt/2271out、34.852秒，后者113298prompt/2698out、39.214秒，均未触输出上限，cached未知。

逐条读取最终原SSE：889/1115个JSON记录，delta键只有role/content，未见reasoning/reasoning_content/reasoning_tokens键或content中的think标记；usage仅prompt/completion/total。只能记录“未见可见reasoning”，不能凭请求flag认定真实内部模式已启用，也不能据字段缺席认定不存在内部推理。prompt差36的原因未知；输出预算不同、时序及并发未控制，不作速度、缓存或能力因果结论，语义采用另由owner按当前源审阅。本试验没有重发已解答案或授Game信用。可复核纯事实对照为 `D:/ck3-state/model-dispatch91/THINKING110-ACTUAL-COMPARISON.json` 与 `REVIEWS91.json` 的mode_comparison，原REQUEST/SSE保留。


### resume91 111–112 的最终采用与新 IP 库存核实

UTC `2026-10-30T21:50:32.134616+00:00` 新IP实际 **126任务/135次POST尝试**，当刻客户端在途1，峰值仍8@20:36:59.164561Z；目标24–32未达到，旧1.7峰25不计入新服务。数字来自EVENTS实际base_url，含登记的M1首任务外部输出路径，不用已封包清单代替HTTP。客户端区间含网络/服务等待，不是服务端推理数。runtime预留1为调度意图，不是服务端硬保留。完整库存与快照在 `D:/ck3-state/model-dispatch91/OPERATIONS-INVENTORY111.json`。

八M逐项核实：M0/M2/M5/M6/M7无完整当前输入且尚未实现的未派READY；M1经理已阶段结束，新库存未知，不为补八队唤醒空岗。M3实际新slot/entry16B已取得并直接POST `m3-ef0-entry144`，后继完整producer原件待真实获取；M4新809B整方法首length、一次诊断纠错完整但语义拒绝，停止同组第三轮。已写候选等待验收与缺真实自然producer/body不是可重派实现，不以旧绿或确定性搜索补并发。后续真实输入仍由owner复用现call91直接并行，不等中央ACK。

`java-read-durability111-scope02` 完整25源487832字符、101335prompt/751out，17.803秒stop却仅分类、没有实现，源码采用0。后续真实拆分 `java-read-binding111-narrow03`（9完整源125506字符，26365in/1345out，11.080秒）产生两方法与四caller，owner生产语义改0，strict2源0/2.050秒；`java-read-evidence111-body04`（11完整源及7片段130241字符，28509in/730out，7.809秒）方法部分采用，owner补廉价ExactRef角色/optional qualification解码，strict1源0/3.671秒。两者均已S/Z并由MB112装载；专门READ计数行为验证仍待完成，不授性能提升或游戏动作。证据在 `D:/ck3-state/resume91-java-delivery/read-durability111/{read-binding-narrow03,read-evidence-body04}/candidate/DELIVERY.json`。

`runtime-no-progress111` 两轮均完整stop/实际OS0：101670in/2761out及102565in/4874out，但Optional嵌套、typed Controller观测、wall/pending/日期及测试API等整候选错误，最终模型生产采用0。owner接管3生产叶+1测试，严格编译0，17P0F0skip/1.881秒；后到的去>=2观察范围另记。运行岗S/Z采用及MB112六源增编0/9.409秒、21:47:50Z同Game LOOP_START/next29是独立运行事实，不追认为模型多叶闭合或运行期决策。原件为 `D:/ck3-state/resume91-runtime/no-progress111/{REVIEW111.md,RESULT111.json}`。

body04封包实际执行PowerShell prepare/readback违反本轮cmd-only，owner已承认，作为操作审计单列；保留原件，不重跑模型/已绿，不将其当模型推理失败。逐项采用以owner最终回执覆盖raw RESULT默认 `adopted:false/NOT_YET_REVIEWED`；whole/fragment、配置/分析、隔离fixture/生产粒度不同，不拼成虚假的统一采用率。


### resume91 再次扩大真实派发与 typed 合同后的采用边界

本轮再次恢复运营的冻结窗口为UTC22:48:46→23:10:57：新IP188→246个真实逻辑任务、201→264次HTTP尝试，新增58任务/63尝试。末刻2个客户端在途，新IP实测峰仍8；目标超过8尚未达到，旧1.7峰25不混入。数字来自标准目录和三个显式external指针的POST_BEGIN/ATTEMPT_END，prepared或owner宣布将发不计BEGIN。有限metrics实际22:52:16 running0/waiting0/KV0、22:58:34 running4/waiting0/KV0.09469697；不能从客户端区间推服务端推理数，也没有证据将峰8视为服务容量上限。后到请求独立滚动，不覆盖此冻结事实。

完整API前缀复用后，Archive三个真实场景、M1 late-cause生产/行为、M2 owner已闭135B typed合同后的C++fixture/Javaoracle、M3 LookupCaseApi的case方法、M6日志生产/测试与时钟负例等均owner直接并行POST；不经过models中央封审/ACK。多轮完整ASM/Host恢复错误的原任务停止，owner掌握语义后再派真正未写的typed方法；不让模型复述已经写完的答案，也不把未知原件包装成READY。M0拟Java物化器在POST前取消，普通Git准备不造模型任务。完整逐请求/库存/实际重试证据为 `D:/ck3-state/model-dispatch91/OPERATIONS-EXPAND115.json`、各任务EVENTS/REQUEST/SSE/RESULT和REVIEWS91。

新增实际采用对照：M6 timeout113的十次真实POST后，owner提供harness、模型有限constructor/三测试方法经真实compiler诊断纠正，五生产源+host严格0/2.776秒，3个新JUnit方法3P0skip/1.501秒；六叶正式97914337c8/S-Z采用分记。unknown-method04请求未带完整直接NativeActionPort record，05补全后修正，不能把该上下文缺口算成“完整API已给仍发明”；完整测试候选失败与owner固定harness成本也保留。证据 `D:/ck3-state/resume91-m6-native/operation-timeout113/{MODEL-REVIEWS.json,MODEL-BOUNDARY-OBSERVATION.md}`。

M0 portable04/05只部分模型配置/生成器加owner修正被采用；其后正式target首次configure0/4.532秒、24TU+link0/79.590秒、registeredCTest1P/0.319秒是新的构建交付验证，没有新增模型调用，也不是raw整候选原样成功。M7 publisher两个完整Host候选拒绝后owner接管Win32/FFM，Scenario/Code局部与owner修正组合，最终3Java严格0、受控RAM8case/146检查通过；不授CK3callee、生产、Game动作或新增日。输入完整源文件数/字符/token、实际改写方法、owner修正/缺上下文、编译与行为结果分别记，不据这些对照给通用能力上限或统一成功率。

详见[可行性](../local-model-executor-feasibility-2026-10-28.md)与[能力边界](../local-model-capability-boundary-2026-10-28.md)。




### resume91 117–118 真实运行决策与请求参数审计增量

有限事件截止为UTC 2026-10-31T00:18:08.629162+00:00，窗口从2026-10-30 18:40开始，首个实际BEGIN为18:49:40.894697。源码候选共450个逻辑任务、499次尝试，截止时450项终态、在途0；其中新地址192.168.1.11为334项/353次，客户端区间峰仍8（20:36:59.164561），没有达到24–32。旧地址历史峰25另列；客户端区间不等于服务端同时推理数，也不能视为容量上限。此截止后的新BEGIN独立记录，不回填成截止时在途。

旧REVIEWS91.json冻结cohort保持字节与SHA不变，新增来源/审阅放REVIEWS91-INCREMENT118.json；原RESULT默认NOT_YET_REVIEWED/adopted=false不能覆盖后到owner回执，未审仍unknown。各状态同时包含整稿、部分、配置、D隔离、生产采用，不能相加成统一成功率。五项Java小批的真实区间仅峰2：A/B在00:05:01–14重叠，bindings在00:05:25–40，lifecycle/finish在00:05:41–54重叠，并非五项同时。

Root Stop4四项真实审阅已纳入：生产首稿为部分采用，真实strict首红BooleanSupplier.get()后，compiler02原样纠正为getAsBoolean、2生产源strict0/2.155秒；测试首轮真实0P1F保留。fixture02保留部分结构，owner补外部flag真实翻转及Wait分支断言后，1新方法+1既有手停恢复方法同JVM2P0F0skip/1.356秒。两生产叶正式5d5629653c/S-Z采用，不把四个HTTP完整回包算四次整稿原样成功，也不授实际在批停止/重启或游戏动作信用。原始raw终态与最终owner采用回执分别保留。

117是本阶段首次真实普通运行期qwen：2026-10-30 23:40:24.2569706Z BEGIN，实际请求1,180,737B；HTTP200，headers43.635秒/有效内容TTFT43.636秒/total44.365秒，23:41:08进入婚姻ActionSelected。随后Cadence mutable head身份审计与callback完整JSON小预算阻断，Native提交0、新增日0。118于23:57:55.1841796Z再次真实请求1,187,609B，200/headers43.888秒/TTFT43.890秒/total44.633秒，仍选婚姻；callback预算已越过，但历史.class SHA审计再次阻断，真实23:58:42 END4/next36，提交/新增日仍0。这里只独立核实117/118两次业务HTTP，不把源码call91调用充作运行期决策，不覆盖后继worker现场，也不抹去此前开局FOCUS的历史决策。

参数勘误：m6-http-progress116-iofailure-method04的minimal input spec虽声明frequency_penalty=0.3，但actual REQUEST.json没有该键；call91 minimal-spec白名单未转发。故该单不是已执行的0.3惩罚参数实验，服务默认值/效果未知。实际REQUEST SHA256为e383593c14deb0c59f16f9a51ca47b85c7e752917eefd4c51687b98ed502857d。只修正运营描述，没有为验证再POST、修改caller或全局配置。

证据：`D:/ck3-state/model-dispatch91/OPERATIONS-INCREMENT118.json`、`REVIEWS91-INCREMENT118.json`、`RUNTIME-ORDINARY-QWEN117-118.json`、`FREQUENCY-PENALTY116-AUDIT.json`；Root四单REVIEW及`D:/ck3-state/resume91-root/stop117/ADOPTION-REVIEW.json`。采集仅标准任务目录、三个显式external事件入口和已知worker stdout，未扫描CAS、未新增模型HTTP。

互链：[可行性](../local-model-executor-feasibility-2026-10-28.md)、[能力边界](../local-model-capability-boundary-2026-10-28.md)。




### resume91 usage120 源审与真实运行 token 观测

Root usage120四单审阅单列为REVIEWS91-USAGE120.json，不回写旧99任务/100尝试冻结cohort或原transport SUMMARY。生产首稿真实strict1/1.635秒为漏BigInteger import；compiler01原样import纠正后strict0/1.917秒、owner生产语义修改0。测试首编7错来自owner classpath漏既有PlanningFixtures，不计模型源码失败；补实际依赖后编译0。首行为1P1F的真实NoSuchFileException来自模型虚构attempt路径，保留失败；fixture02修真实文件引用及负例后，owner再补单次调用、exact-zero、两usage对象替换三组断言，最终2新method同JVM2P0skip/7次软件HTTP、Java0/2.131秒。此时共享采用/装载尚未获回执，不预授loaded、真实运行usage捕获或Game动作信用。

已知worker117/118/119/120的原stdout分别记录1/1/4/1次完整ordinary HTTP END，共7次；Root/运行岗确认均返回SELECT、Native提交仍0。独立精确读取119末次与120的last_plan visit.evidence.model_decision_receipt→attempt，不枚举CAS，也未打开1.2MB request body；两份raw SSE各14,217B和15,598B，均小于20KiB。usage行实际choices非空但delta={}、没有有效content，因此仍应保留usage对象；不是只有choices=[]才可能带usage。

| 运行样本 | request bytes | reported prompt | completion | total | cached |
| --- | ---: | ---: | ---: | ---: | --- |
| 119第4次 | 1,207,885 | 341,236 | 142 | 341,378 | null，未报告 |
| 120 | 1,213,368 | 342,785 | 142 | 342,927 | null，未报告 |

这些数字来自两份原始SSE的reported usage，不由字节数估算token；cached缺字段保持null，不能当作0、缓存未命中或命中证据。也不从两个不同请求的耗时/大小推出缓存因果或能力上限。精确反链、原usage对象及每worker真实HTTP计数在`D:/ck3-state/model-dispatch91/RUNTIME-ORDINARY-REPORTED-USAGE120.json`；四项REVIEW与`D:/ck3-state/resume91-root/usage120/DELIVERY.json`另列源采用事实。本次仅只读已知记录，无新增HTTP、API探测、Native查询或CAS扫描。


### resume91 rolling122 冻结运营、后到回执与运行采用

固定快照为UTC 2026-10-31T01:07:39.156291+00:00，原件`D:/ck3-state/model-dispatch91/ROLLING122-010739.json`。源码候选累计507个逻辑任务/557次尝试，新地址192.168.1.11为391项/411次，截止当刻客户端在途4，历史区间峰8。同期metrics为running4、waiting0、KV0.0845959596；这些均为该时点观察，客户端POST区间不等于服务端同时推理数，也不表示容量上限或后续永久状态。后继BEGIN/END不回填此窗口。

源审另有较早截止：`REVIEWS91-INCREMENT122.json`冻结至00:58:45.140819，新增审阅32任务/33尝试，分组为raw method/body5、owner纠正测试4、owner纠正源码3、拒绝18、部分研究分析1、未选用诊断原型1。旧118 cohort的10项unknown获得后到回执，仅追加补记；`REVIEWS91.json`、`REVIEWS91-INCREMENT118.json`与`REVIEWS91-USAGE120.json`三个基线未改。分组包含不同采用粒度，不能合成整稿成功率，HTTP终态也不能替代owner审阅。

后到M4原件单列，未并入上述源审截止。329首384例Native差分0失败、核对44,051个完整40B backing slots；边界为原329到标准copy及opaque776，未执行原776/copy1653完整body。producer R2原样采用，core两轮拒绝后owner接管（相对被拒稿+41/−73行），consumer保留模型stream/codec并由owner修补+31/−40行。新776 producer R2经owner仅score-prefix修补+21/−47行，单源strict0/0.675秒、首次512例生成0/0.271秒、44,600 slots；809 producer R2零Java修改，单源strict0/0.685秒、首次384例生成0/0.293秒、65,312 slots。这两项是生成回执，尚非Native差分；776 core/窄forward截断及809 pairphase两轮源拒、owner core/wrapper接管成本分别保留，不授full809、正式部署或Game信用。原件为`D:/ck3-state/resume91-m4-native/merge329-single91/ACTUAL-ACCEPTANCE01.json`及`merge776-single91/INPUTS-ACTUAL03.json`、`sort809-single91/INPUTS-ACTUAL03.json`与各SOURCE-REVIEW。

时间勘误按实际`EVENTS.jsonl`：`m4-merge776-inputs91`的ATTEMPT_END为01:04:51.813943，早于`m4-sort809-inputs91`的POST_BEGIN 01:05:07.144992；这两个首轮producer请求没有重叠。未poll标签或宣布将发不计在途。

usage120后到正式采用回执为`D:/ck3-state/resume91-root/usage120/LIVE-ADOPTION122.json`：正式commit `6d7f6a74f6`已实际装载MB121，补充此前“尚未获回执”的历史时点。worker121/122各新增一次完整ordinary HTTP，与117–120已核实的7次合为9次；业务请求与上述源码候选数分别统计。

| 运行样本 | reported prompt | completion | total | cached |
| --- | ---: | ---: | ---: | --- |
| 121 | 344,340 | 137 | 344,477 | null，未报告 |
| 122 | 345,900 | 139 | 346,039 | null，未报告 |

这些是实际运行的reported usage；缺cached字段不作0或命中判断。正式源码采用、MB装载、运行期HTTP已分别有回执，usage本身授予的Native提交信用仍0，不外推APPLIED、SAVE或新增游戏日。本文档编写仅读取上述已有原件，未额外新增模型POST或编测。


### resume91 rolling126 冻结运营与后到采用

UTC 2026-10-31T01:43:10.791756快照（`D:/ck3-state/model-dispatch91/STATUS-ROLL126-014310.json`、`ROLLING126-014310.json`）：新IP累计432任务/454尝试、当刻在途0；00:58:45之后64任务/66尝试全部终态，该阶段客户端区间峰6（01:12:02.295081），新IP历史峰仍8（20:36:59.164561）。旧IP峰25另列，客户端区间不等于服务端推理并发；运营监视不计模型任务，后继POST不扩此窗口。

`REVIEWS91-LATE-ALIAS-M7-123.json`补记Root alias五单：compiler纠正原样strict0、owner生产语义修改0；两项独立新测试均绿，分次调用，非同JVM2P。第三次fixture候选代码拒绝后，owner仅重跑此前失败负例1P，不能算三份测试整稿采用。实际122归档样本离线从1,224,362降至800,340B，833行完整typed还原；该离线样本/本包当时尚未获自然加载回执，无token、cache或速度实测结论。旧冻结review与raw transport记录保留。

M7正式Java `d17b7d9580`、Native `c703f434d2`分记：两C++ core函数原样、owner算法修改0；同commit header/core/test/module的minimal CMake wrapper完成2TU/link/CTest，14case/781checks。Java6生产源、2JUnit、7P覆盖14scenarios；其他CI/adapter测试多处为部分采用加owner修补。15次POST的包内峰4并非全服务峰，不授fullRoot/runtime/Bridge archive或hosted CI通过。精确回执为`production-idler91/FINAL-BINDINGS03.json`。

冷回放整稿源拒与M4有限producer/源审范围见[可行性](../local-model-executor-feasibility-2026-10-28.md)、[能力边界](../local-model-capability-boundary-2026-10-28.md)。本次文档交付0POST、0编测，不否认此前真实运营观察；未改配置，后继review分布待实际回执补记。


### resume91 review126 后到审阅补记

此前“分布待收”现获补记：`REVIEWS91-INCREMENT126.json`固定01:43:10截止，21任务/21尝试均stop、21项owner审阅齐；原OS18项0/Root3项未知，未知非拒绝。

异质分组：raw纠正2/scope3、owner test4/source1/Native fixture1、reject6、model helper纠正1、analysis/code拒1、cast cleanup1、direction部分1，合21，不算统一采用率。增量客户端峰3@01:32:59，阶段6/新IP历史8另列；旧5份SHA及Root旧unknown/M7后到补记不回写，后继HTTP不扩窗。本包0POST/编测。


### resume91 parallel128 实际并发要求与串行空档

用户反复要求更多真实同时请求，累计调用数、参数、未poll会话或准备任务不能代替。Root承认准备/审阅串行空档：服务余量观察下峰8仍不足，须改进组织，不能用“服务不支持”解释；观察也非最大容量证明。

完整源齐后owner复用call91立即直POST，无需中央ACK；implementation与独立consumer/probe并行，审阅时下一未写方法继续。source_files+task_path自动三消息，免手工巨大body/额外索引前置；MB HOLD只编测，不挡HTTP。12–16为真实积压时初始在途目标，非已达/已实现scheduler，非quota，不凑数。复用caller、不建平台、不造任务/重绿，监视/总结不计模型请求。

`STATUS-PARALLEL128-021352.json`固定02:13:52.729045：源在途1项m7-captured79e-cells92；server running1/wait0/KV0.0214646。新IP历史峰8尚未达目标，旧IP25不混；源码与运行期HTTP分记。后到两root-clock REVIEW为raw D采用、owner语义0、合并strict2src0，不授runtime/Game信用。本包0POST/编测/CAS，不阻128运行。


### resume91 portable128 跨机复用与实际并发规则

用户要求将新心得、经验与规则提交GitHub供其他机器worker复用。入口为[worker指南](../local-model-worker-guide.md)与[统一配置](../local-model-executor-config.json)。本页D路径仅是本机证据/caller记录，不是跨机依赖；其他机器使用自己的machine_id、获准数据根及caller，不复制本机state/账本，不据文档操作Game。

完整直接API与当前源码置前，唯一任务、真实诊断及返工要求置末，保持配置三消息。source_files+task_path复用caller自动封包，避免手工巨大body或额外索引前置；owner源齐即可直POST，无需中央ACK。实现与独立consumer/probe并行，审阅时继续下一未写方法；MB HOLD限编测。累计调用、参数、准备队列、未poll标签和监视不能代替实际请求并发，不造任务/重绿凑数。

`D:/ck3-state/model-dispatch91/WINDOW128-022010.json`固定02:10:10→02:20:10：27新任务/27真实POST、28 END，客户端区间峰4、末刻源0/服务running0/wait0/KV0；END可含窗前已在途请求，不等于28新任务。新IP历史峰8仍不足，旧IP峰25另列；该观察不证明服务最大容量。源码候选与实际运行期HTTP分账。

两个root-clock REVIEW均原样D采用，owner生产语义修改0，同次strict2源0；首命令把-J选项误放argfile、尚未编源就退出，是owner命令成本，不算模型源码失败。记录入口为两`root-clock-*-audit128/REVIEW.json`，不授运行装载/Game信用。源审分组仍以`REVIEWS91-INCREMENT126.json`及后到回执为准，异质结果不合成统一采用率；本包0POST/编测/CAS，不等待大cohort。

运行owner后到报告：worker129于02:31:16.0517311Z实际请求342,745B，200完整返回13.633秒（headers12.872/TTFT12.873）；reported101066/142/101208，cached=null。seq276普通qwen CROWN于02:31:39.332提交，02:31:44.093独立确认law0→1/prestige220m→200m、APPLIED；本轮新增普通APPLIED1，与旧FOCUS分开，新增日0。末plan pendingwait/brief票空不否此前HTTP；后继replay合同故障END/next47不重放已应用动作。证据`D:/ck3-state/resume90-runtime/worker129.stdout.log`；不同请求的payload/token/时延不推alias或cache因果，本文未另读CAS。


### resume91 review131 冻结源窗与后到审阅

源HTTP窗固定UTC 02:20:10.328905→02:54:14.974288：49任务、52 BEGIN/51 END，截止时1项在途，窗口客户端区间峰4，新IP历史峰8；12–16目标未达，不能用累计数代替同时请求，也不由客户端区间推服务端并发。截止时在途的m4-selector880-native-inputs91后于02:54:54结束并获源拒回执，不回填成截止时已终态。

冻结主表分组：6项原样采纳，具体生产/隔离scope按owner回执；2项仅源接受待编、14项部分采用、22项拒绝、3项仅分析、2项当刻未知。方法名hunk、循环删除、完整方法、测试与分析的粒度不同，不合成统一采用率；后到源审/行为与正式发表另外记，raw SUMMARY默认adopted=false不替代owner回执。主表及旧记录保持原字节。

M1 Crown R2后到selector回执于03:04:59完成baseline RED→candidate GREEN，零owner语义修改；M7后到memory原样及单NaN方法参与8JUnit绿，但套件使用owner core和其他owner测试，均不回填冻结分类或授完整生产/运行因果。精确范围在后两页补记。

证据为`D:/ck3-state/model-dispatch91/REVIEWS91-INCREMENT131.json`和`REVIEWS91-LATE131-0308.json`，两份SHA已核对；固定源窗不因后继任务扩大。本文档交付0模型POST/GET、0编测/CAS，不改旧review/source SUMMARY，不作为source owner直POST或runtime的门。


### resume91 peak149：新地址首次峰14，持续时间另计

固定UTC07:30:27.462103→07:40:27.462103源调用窗口有35个新任务、36次真实POST，截止26次END（21stop、4length、1reset），10次仍在途。新IP实际客户端峰14发生07:39:58.637575→07:40:02.177609，仅3.540034秒；至少12在途共9.803132秒，至少10共20.404558秒，十分钟平均2.0054。旧报告中的峰8保留原时点事实；本次只证明首次峰值达到初始12–16区间，不是持续达标。

截止单刻9项已有有效content、1项待headers；服务running10/waiting0/KV0.2853535。35个任务数不代替并发，客户端峰也不代替服务推理峰。26个已终态attempt的content TTFT中位4.094秒、p95约15.848秒；未终态不估算，缺cached字段不推命中。reset按既有配置重试并保留partial，不归为实现能力失败。

该波来自M1真实public UNAVAILABLE0/CI材料、M3新注册record、M4新Full880–Free83组合及首次非法wire测试、M7新cleanup桥及独立测试、M0和Root真实CI诊断。完整输入owner直接POST，无新增调度平台、空探测或旧绿重投；HTTPstop、源审、必要编测、正式采用仍分别记录。原始界限见本机`WINDOW128-074027.json`、`STATUS-PEAK149-074027.json`、`ROLLING-PEAK149-074027.json`与`PEAK149-ANALYSIS.json`，位于D:/ck3-state/model-dispatch91；这些是机器本地出处，不是其他worker使用服务的前置。本文档追加不新增模型POST或编测。


### resume91 CI149 后到验收：四次调用与三项行为通过分别记录

Root 后到回执给出 2026-10-31T07:52:49.843115Z 的实际结束结果：6 个当前生产源 strict 通过，两个测试候选 strict 通过，原有 3 个目标方法在同一 JVM 中 3P/0skip。四次真实源码 HTTP 均 stop，但首稿两项拒绝、纠正后两项部分采用；whole raw candidate 采用为 0。本轮未修改生产代码、未重跑 hosted CI、未执行外机分支，不授 Game 或已加载产物信用。

编测成本分开保留：首次 baseline strict 漏既有 Regression 依赖，首次 Reg 两方法运行缺 jna.tmpdir，均属 owner 的命令/环境错误；补依赖后 strict 通过，仅重跑修正 JVM 参数的 Reg 两方法 2P。Defender 的 LF 哈希断言失败是真实基线问题。早先已发表的“当时尚未编测”及其 payload/SHA 不回写，本段记录后到事实。

证据为 Root 的 ci149/DELIVERY.json、四个标准任务目录的最终 REVIEW.json 与原始编测回执。此次经验更新复用这些原件，没有新增模型请求或验证重跑；正式源码是否采用另以唯一 writer 的 Git 回执为准。

### resume91 墙钟对齐的连接重置有限观察（2026-10-31 12:34Z）

固定窗口为 UTC `[2026-10-31T06:30:00Z, 2026-10-31T12:30:00Z)`。只读 `D:/ck3-state/model-dispatch91/*/EVENTS.jsonl` 标准一级任务根，筛选实际 `ATTEMPT_END`、`base_url` 为当前 `192.168.1.11:8080`，且 `failure` 含 `10054` 或不分大小写的 `reset`；不含另列的自定义输出根，也不将 ordinary runtime 决策 HTTP 混入源码任务。此口径共 35 次失败尝试，未新增模型请求或为本诊断新增服务 GET。

35 次均落在 UTC 分钟除以 10 余 8 的附近：其中 34 次在第 10–11 秒，另一次为 `09:08:09.955545Z`。请求从实际开始到 reset 的耗时最小 0.117682 秒、中位数 10.834317 秒、最大 132.356721 秒，因此这组样本并非相同请求运行时长后才失败。该规律只描述已观察到的共同墙钟相关事件；服务定时任务、代理、网络或其它具体根因仍为 unknown，不能据此断言因果或模型语义能力。

最新两个可直接复核的标准原件如下；均为各自 attempt1，后继配置内重试不算新的语义轮：

- `D:/ck3-state/model-dispatch91/m2-family-child-default172/EVENTS.jsonl`：`12:28:10.557211Z` reset，请求已运行 16.327252 秒。
- `D:/ck3-state/model-dispatch91/m1-government-shared-composition168-book02/EVENTS.jsonl`：`12:28:10.557642Z` reset，请求已运行 51.172753 秒。

部分 SSE 保留但不拼接或采用，按现有最多 6 次 HTTP 瞬时错误退避策略重试完整原请求；本观察不修改 caller、参数或重试策略，也不授权重放任何 Game/UNKNOWN 动作。完整响应的源码拒绝与 `length` 另行归类，不能将这 35 次连接重置合并为模型源码失败。

### resume91 中断请求、输出碰撞与有限窗口（2026-10-31 14:30Z）

本轮明确继续执行；历史休假段不产生新停止。运营在14:15:28Z首个有限扫描看到4个未闭区间，其中2个是13:57的旧M4请求。14:16:16 Win32实际无call91进程；这两个原SSE都没有DONE/finish/usage、JSON半截，最后mtime13:57:48.483139Z。保原EVENTS，不补造ATTEMPT_END；新M4 owner在14:19:05真实以新唯一目录恢复完整请求。14:30:18.556685Z另一次Win32读回恰有2个实际call91进程，分别为M4 fresh-method175和M5 normalize-full174-core；原旧日志仍不能计当前在途。

冻结口径：`D:/ck3-state/model-dispatch91/context-support175/WINDOW175-143018.json`，源码EVENTS截止14:30:18.267958Z，十分钟窗起14:20:18.267958Z。真实57 POST/57 END，40stop/15length/2reset；本次接续峰12的区间为14:20:51.673164–14:21:01.308690Z（9.635526秒）和14:23:44.135357–14:23:48.276674Z（4.141317秒），合13.776843秒，不是持续12–16。当前有效源码在途2，随后服务metrics running2/waiting0/KV0.045454545454545414；事件扫描14:30:17.042481–18.221614Z、metrics GET18.221628–18.264831Z，非原子。排除运行期普通决策HTTP；不把snapshot之后的新POST回填这个窗口，不以HTTP或软件结果授游戏日。

另有真实输出目录碰撞：m3-global-wrapper166-method和m3-global-wrapper166-binding于14:19:33.908398/.908454Z并行POST，owner误把公共调用器根当两者输出目录。方法正文丢失不可采用，最后binder正文幸存但候选也被审拒；REQUEST损坏，第二个BEGIN在公共EVENTS中也丢失，不能从started_at反造POST时刻。两份真实工具回执与owner事故记录在`D:/ck3-state/resume91-m3-native/registration-allocator-global166/owner-output-collision01/OWNER-ERROR.json`。严格源日志计数与该单列缺失记录分开；碰撞在上述十分钟窗以前，不影响57/57和峰12。已实际发送的两请求不因碰撞归零，但也不伪装成可审候选。必要 replacement/correction用了唯一标准任务根，真实完成并由owner分级采用。

现有call91.py仅补一项针对真实故障的输出隔离：解析输出路径若等于该调用器公共根，则在mkdir/读request/POST以前退出。本次一次无HTTP负例实际exit1/约0.035秒、明确拒绝；未触旧碰撞原件，正常独占目录、固定三消息、参数、重试和游戏行为均无改动。其它机器不用取得此D盘脚本，但也应隔离每个并行任务的请求/响应路径。候选源码、软件编验、正式发表、运行装载、APPLIED和新游戏日继续分开。

### resume91 reader按attempt修复与实际采用（2026-10-31 14:57Z）

本机既有observe91.py、rolling122_snapshot.py、window_last10_128.py已修两份旧M4未闭日志对当前活性的污染，保原raw区间及未知实际END。后继又修按整个task排除造成的新attempt误判：实际目录+task+attempt+原POST限定当前排除，独立新attempt仍保活；rolling消费者也按目录限定。固定两份中断观察及Win32/SSE读回保在`INTERRUPTED-CALLERS175.json`及`context-support175/CALLER-READBACK175-143018.json`，不添加逐POST探测、来源审计门或自动重发。

新未写边界采用真实模型先行：models-interruption-attempt176与models-interruption-probe176于14:47:06.474991/.487792Z并行POST，分别stop26.3435秒、length4500/49.1476秒；首整份修改因具体代码错误编前拒绝，截断probe整份拒。收窄的-correct02两单于14:50:47.172350/.162935Z并行POST，helper stop7.2827秒/5031+818，probe stop19.3382秒/3197+2757、cached均null。纯helper算法partial采用，owner修1处Windows Path语义和3处宽异常，完整reader装配由owner接管；第二份probe仍虚构ast.compile、时间预期和异目录输入错误，未执行即拒，不追认任何模型测试成功。owner新紧凑10数据例首次实际exit0/0.0355053秒；14:54:56.012394Z采用到既有两reader，14:54:59.270949Z真实无metrics运行exit0。四标准任务根REVIEW.json均写实际分级，未改原SUMMARY/EVENTS/旧冻结cohort。新生产Java、Main装载、Native、Game动作及新增日均未由此获得信用。

最新自然观测14:57:38.874162Z，距上次metrics约27分钟，仅一次GET。源码有效在途0，旧2只留raw；随后服务running0/waiting0/KV0，分阶段非原子。前十分钟23POST/26END、峰3，21stop/4length/1reset；`WINDOW128-145738.json`及当前STATUS/ROLLING保细节，不以14:20短峰12替代当前空闲，也不以无需求调用凑使用量。

## 2026-10-31 16:00Z：P0 C179、有限 witness 与固定十分钟窗口

Main P0 C域 `fresh-cold-domain179` 实际15:39:21.386532→15:40:00.412612Z，200/stop39.026秒、reported93839+3322/cachednull；5叶源审拒，未编坏稿。首输入遗漏6个实际类型定义由owner负责。补完整API后 `fresh-cold-domain179-r2` 15:44:46.024826→15:44:56.569867Z，stop10.545秒、106455+1334/null，只纠正 Primitive 与 LifeReplay；前者 raw 执行算法，后者 partial+owner exactref/唯一source角色，另外 Clock/Evidence/Pause3叶 owner。仅5新src strict15:48:46.474170–48.111645Z exit0/1.637480秒，候选已交唯一runtime owner；当时无真实新worker/cold恢复成功信用，后继以运行回执更新。

独立 M2 role187 的4真实POST均stop；host R2 保留顺序脚本算法但 owner 修 Java capture/真实 Resolved 类型，两个 literalbook 完整稿均拒。R2和首稿完整 content 逐字同SHA5bbf8b29bd24ba1e6cff3bc7b6e25419c893f486fddccd701d9dbc50900a23d0，实际REQUEST SHA不同，只记重复候选、不推缓存/后端原因。owner 独立4literal+该部分host实际首次4src strict0/.637388秒、4场0/.143248秒，END15:46:43.031306Z；原件 `role-resolution187/witness-owner/REPEATED-CASES187.json` 及同187根的 `build/JAVAC187/ACTUAL.json`、`build/RUN187/ACTUAL.json`。Wait179的5task/6实际POST为3stop2length1reset，core算法raw/consumer算法加机械API修，三fixture任务0源码采用；owner新两分支与1 actual Header→Wait组合首跑通过，15:56:36.789608Z END，0旧Header5场重测/Native/Game。

一次既有reader+metrics自然观察截止15:57:31.923727Z：实际当前source3（原未闭5减2个已观察中断旧attempt），后相位全服务running3/waiting0/KV0.0782828，非原子。固定15:47:31.923727–15:57:31.923727十分钟29真实POST/25END（21stop4length）、客户端区间峰6@15:56:49.952670，当前3为 M1 footer181 core/literal/notify。持续12–16及24–32仍目标，不能把早先短峰12、累计任务或新派岗算当前。原件 `WINDOW128-155731.json`；本次owner漏先rolling导致一次cutoff断言红保留，补既有依赖后同cutoff出报告，无第二GET/新平台/额外模型调用。普通运行决策HTTP仍由runtime独占且不计源码窗口。

## resume91 181 后继源码采用与包装经验（固定证据批次）

机械输出边界：`m0-heap-formal-relocate176-01` 原23个 package/import 编辑、9新 namespace TU strict0；M3 `portable-delivery172/test-owner/DELIVERY172.json` 七份42.8KB整源回传 length12000/145.209秒整拒，owner 词法迁移，后继20新源 strict0。完整输入规模不是实际修改规模，亦非模型通用规模上限。两项沿原请求和回执，无为文档补 POST/测试。

M1 新有限依据见执行机 `government-cold-manager184/LOCAL-MODEL-LESSONS184.json`：182完整祖源中无关 Calls 混入、185无0x的 owner 提示歧义；184两完整 stop 稿仍漏唯一新桥，全0采用。相对的新185 actual183 consumer 单 POST9.479秒/1433输出，正文/literal保留且仅机械 imports 后首 strict0/实际case0；186两R2生产正文原样首 strict及46断言0。只授具体叶，不由短方法/stop或最终组绿概括稳定能力。M2 207/208 casebook 纠稿返回生产类整拒，有限两轮后 owner 接管，不第三次刷同题。

Root SAVE181 实现两真请求 stop10.530/13.144秒，reported19464+1099、19549+1572；record/codec 可用，effects 的允许同ID被写成必须同ID由 owner 纠正。独立 probe 第三请求 stop24.941秒/24715+3740，owner 修 API/合法 fixture/负例后首26 checks0；`resume91-root/save-codec181/DELIVERY.json` 分记三叶、测试来源及0物理信用。cached均null，无缓存收益结论。它不授本次冷 SAVE、Native或新游戏日成功。

正式包装经验来自 Native writer 对 M2 193十叶的无EOF marker/逐Git blob核实；本岗 `resume91-runtime/save-cold181/RAW-SHA-ERRATA181.json` 另保两 READY 字段将LF文本SHA误标raw的 owner 勘误，实际 Service/collector 首 strict回执已按真实 read_bytes 哈希，源码未为勘误变化或重编。该批只整理既有证据，不统计新当刻在途/全局峰，不新增模型请求或编测。

## resume91 183 后继封包勘误与17:44有限负载

SAVE181 Root/runtime 已确认 prepare 的 CRLF decode/default Windows write_text 造成 CRCRLF/双空行，模型 old 串相同格式来自 owner 输入；RAW-SHA-ERRATA 与冻结请求保留，逻辑 LF/actual raw 两个 SHA 分开。此条撤销“模型自行双倍空行”的归因，不撤销实际 effects 约束词、probe API/fixture 等错误。M5 `crt4223-source185/consumer-owner/DELIVERY03.json` 首稿 length4000 因附加 review_points 重复整拒，唯一 source-only 纠正 stop/1087输出，正文与旧可见源相同后采用，不反授首稿。M2 226 DATA JSON 格式正确但 signed/偏移语义仍拒；M3 `m3-registry-portsfixture176` 17:42:44.797401–52.073127 的实际新 POST 与已写 owner 交叉，候选0采用，单列协调失误而非新组件。

既有 reader 顺序执行，source 截止17:44:11.917093Z；固定17:34:11.917093–17:44:11.917093十分钟17真实 POST/16 END（13stop、2length、1reset），客户端峰4@17:43:59.126951。该刻 source3为 M2 method237 与 M6 core/data183；后相位单 metrics 全服务 running2/waiting0/KV0.0378788，事件扫描17:44:10.603886–11.867580、metrics11.867590–11.912436，非原子。已补 Root183两私有根/M5 consumer185两私有根指针；后补 M5 consumer187两根同 cutoff 重算也不改本窗口数字（两调用均窗外已END），无第二GET，初始窗口字节另存。标准根和此前 M3私有174/176同计，窗口原件 `WINDOW128-174411.json`。持续12–16/24–32仍未达；历史 raw17包含两旧未闭 attempt，known-absent 界线另保，rolling 阶段峰15亦非当前。准备或已END迟消费均不计在途；统计未新增模型 POST/重测。随后真正新372B witness237 host/book 17:45:58.796683/.796746Z 实际并发 POST，独立5完整源13034B、4500/8000预算，不冒为此前快照在途。

成熟验证单列：本岗 M3 175 四逻辑/六真实 transport（两reset、一次stop、三length）模型源码全拒，owner core/ASM脚本首次4显式源 strict0、五新场0，未授原生 ABI/Game；M2 216 两整模型拒后 owner 独立 consumer 原样被生产岗首编，首次消费原381B六场完整 RAM/AL/log 差分0。所有原请求、source拒绝和 owner 验证分开保留，未为本段重跑或发表新增游戏信用。

## 2026-10-31 18:44Z：声明缺口勘误、有限软件采用与新窗口

本轮继续 `192.168.1.11:8080/v1 / qwen38-coder`，没有旧 IP 回退。M3 178 的实际 REQUEST 审计发现 rank/book R2 没带目标三参 select/Bytes/Case 声明，只写“same API”，故错签名/缺 records 不能全归模型无视完整 API；main 的目标 API 已给，不受此勘误。原六请求全0源码采用，owner 接管，不第三轮。M6 copy163 的同类漏签名与本岗177 host 入口缺失按 owner 上下文责任分记。跨机器规则现要求每轮实际前缀含完整目标声明，而非依赖上轮。

M1 新 actual183 sentinel→185(15B)→186(72B) 是新消费边，不是旧 case 第三重投。单 POST 9.479秒、1433输出 token，正文/固定 literal 可用，仅 nested/static imports 机械修后，新 test strict0/.578202秒、实际新 case0/.154719秒，保完整 parent N/RET、低 EAX0/高 RAX非0等有限观察。M4 186 则经逐 EVENTS 审计更正为六逻辑任务七次 transport、区间峰1；两个 Book 区间17:31:14–17:32:02与17:32:33–17:33:41没有重叠。5JUnit覆盖7输入通过不追授两个坏 Book。Root save-proof186 的 WriterContracts.Head 曾被 owner 错报不存在，已按实际 Transitions450/459更正；其它候选拒绝理由和首次 strict 历史不改。

本岗177 三角色各两轮共6POST，whole 源码全拒；core/host R2 实际 full REQUEST 带 frequency_penalty=0.3，但任务/诊断同时变化，无 A/B、backend 生效或收益结论。owner core/host 与未读 target 的独立 owner Book，首次6显式源 strict0/.776425秒，首次3场82步0/.889001秒；只授该软件投影，不授原ABI/Native/Game。M2 237 四模型 whole 同样全拒，独立 owner 三源 byte-exact 在239首次4源strict0/.851265秒、4场49步0/.196979秒，未执行原372B Native。M2 250 新 compound consumer 两语义轮/3POST（含18:38:10 reset后同请求完整重试）whole均编前拒，owner 独立15410B源准备就绪，尚无编/Native信用；没有为补并发做R3。

P0 Service186 两真实实现请求 stop23.999/10.257秒，reported89260+1810、104464+1281、cached均null；首callback/query形状部分采用并由owner修 binding/有限窗口，第二小helper的Head恒真式与遗漏校验源码拒绝，helper由owner完整接管。首次单Service strict0/1.723207秒后，owner origin匹配改为实际 acceptsGuard，必要单叶增编0/1.544962秒；首回执保留。该 source/strict 不等于原 SAVE 的 SAVE_CONFIRMED 提交或 Seed/实机成功，仍由唯一运行 owner按实际回执计。

自然 checkpoint 仅复用现 reader 一次 metrics GET。固定18:34:04.862634–18:44:04.862634Z：21个新首POST任务、22实际POST、24END（21stop/2length/1reset），窗口真实客户端峰5于18:42:45.106397Z；采样源码0，随后服务running0/waiting0/KV0，持续12–16/24–32仍未达。source扫描18:44:03.532770–04.809465，metrics04.809475–04.860171，非原子。新补 Root proof/3route/3video、M5189和M3 main178四私有目录的12条实际 EVENTS 指针，无新模型调用、benchmark、CAS扫描或旧绿重测；原两未闭中断区间保未知结束时刻，不计当前在途。窗口原件 `WINDOW128-184404.json`。
