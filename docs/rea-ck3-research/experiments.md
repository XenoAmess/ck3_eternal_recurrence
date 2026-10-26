# REA / CK3 实验记录

machine_id：`xenoamess-full-tower-eb9d2c1186`。本页截至2026-10-26 UTC；完整原件在D盘，来源见 [sources.json](sources.json)。resume62 六类实验按原指令收尾；后继 resume63 在新授权、新容量及新窗口内完成的有限题另列末段，旧关闭与失败不变。

已完成六类实验：同低层命令对照、两轮未修补冷启动、修补后冷分析、106 B机制片段、232 B机制闭包、已持Evidence复用。尚无受控模型token或整体研究提速证据；实际能复用/导出证据，与能回答机制问题分别验收。

## 固定输入、安装与一次性接入成本

原PE来源合同为CK3 1.20.0.4 / Steam25734779，101,040,248 B，SHA256：
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
原生实验鲜读身份和file-backed映射；最后Evidence-only实验只消费历史记录，不重新读取/核hash PE，不授Loaded或实机资格。

实际安装/使用REA6.8.0、D盘Node24.22.1、Rizin0.9.1、Ghidra12.1.4，复用C:/jdk-21（21.0.10+7）。系统默认Node24.14.1不满足该版engines；没有用它冒充依赖通过。npm发布源码记录160d821ac9a0310afcb8d1fc427862dd6508add5，main观察7d36d172ab9b1718630a8e8646f87e7dfdbfc71a；provenance未独立验签。下载/校验/安装/doctor及失败原件均保留，未改全局PATH/MCP配置，未上传目标。

doctor一次真实峰值2,651,537,408 B，后续定位前置Java未设堆参数；这是接入诊断，不能称REA常驻2.6 GB。安装与探测经历多阶段，未做可比较的总安装墙钟计量；[安装/版本/doctor精确索引](sources.json) 保留实际文件与终态。后续不把一次性安装、冷启动、同会话复用混成一种成本。

## 实验一：同低层Rizin命令

同一原PE、同一provider、同命令分别直接执行与经REA执行；未截断，指令/局部CFG及xref匹配保留真值，各受管终态exit0/Job0。

| 目标 | 直接child | REA child | 增量 | stdout直接/REA |
| --- | ---: | ---: | ---: | ---: |
| 2C0F1A0 / 92 B | 5.3281596 s | 8.9364470 s | 3.6082874 s | 10890/28498 B |
| 2A6CE70 / 1799 B | 4.6009657 s | 6.4378178 s | 1.8368521 s | 200116/455524 B |

仅各一对样本。92 B为27条指令、两call 2C0EE50、实际还读R8B；它是cached ticking差值聚合，不是当前goal-control verdict。1799 B为427条、80个内部直接跳转、108块/177边；row marker/局部count递减不证明物理移除。Rizin猜出的两个参数漏R8B，不能把自动签名当ABI。agfj/pdc错误也可exit0，已改用实际有效的agf json并核stderr。

纯Capstone解码约0.0002725/0.0025834 s，不含PE导入、CFG、xref、证据封装，不能与上述全流程直接比。Rizin同一个-c内重复CFG约2–4/52–63 ms，不是跨CLI缓存。输出字节倍数不是token倍数。

[阶段一报告](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/REA-EVALUATION-STAGE01.md)；
[比较原件](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/COMPARISON-STAGE01.json)；
[独立decode基线](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/BASELINE-CAPSTONE01.json)。

## 实验二：未修补Windows冷启动失败

官方MCP SDK2.3.1 initialize/list_tools/open_binary实际成功，随后首个伪代码请求触及资源界限。

| 次数 | Job界限B | 实际峰值B | child墙钟/退出 |
| --- | ---: | ---: | --- |
| cold01 | 3221225472 | 3253211136 | 15.8848201 s / 124 |
| cold02 | 3758096384 | 5393715200 | 12.3832038 s / 124 |

两次三MATCH/最终Job0，无成功伪代码、无warm、未完成graceful MCP close；峰值越界事实保留。hs_err指出前置Java默认G1尝试映射2,113,929,216 B，默认MaxHeap31,675,383,808 B；主JVM堆配置未约束其前置探测。实际Windows路径经batch，不用POSIX启动语义解释。

[阶段二报告](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/REA-EVALUATION-STAGE02.md)；
[两失败比较](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/COMPARISON-STAGE02.json)。

## 实验三：LOCAL_PATCHED冷分析超时

经Root批准，仅D盘launch.bat七个前置Java调用加-Xms32m/-Xmx192m，保留原件8794 B与补丁后8913 B的SHA/diff。最终main实际-Xms32m/-Xmx1536M，cpu.core.limit及GC/CI线程设2；不是全部原生线程硬CPU2。未改Shared、REA源码、全局JDK或主堆，标识必须为LOCAL_PATCHED。

同MCP会话计划查询同92 B函数两次；open_binary7.3196221 s成功，但实际仍为whole-PE import/default autoanalysis，首pseudo901.0241796 s返回provider_timeout。child909.426672099 s，outer912.6354189 s，峰值3,310,661,632 B低于3.5 GiB；成功pseudo/warm均0。没有新的已确认OOME，不再增预算/重跑。

close_binary0.0068693 s、client.close0.2070172 s完成，三MATCH/Job0，私有项目/快照删除。DB实际在tmp路径；原index768 MiB估计不足，前向重配仍在原1.5 GiB内，不能双算一般TMP/DB或追认旧估计通过。收场tools native allocation2,063,588,136 B。

[阶段三报告](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/REA-EVALUATION-STAGE03.md)；
[比较原件](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/COMPARISON-STAGE03.json)；
[RPC/终态](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/GHIDRA-MCP-COLD03-RESULT.json)；
[安装补丁原件/diff](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/config/LAUNCH-BAT-HELPER-HEAP-PATCH01.json)。

## 机制case一：106 B局部验证，逻辑未闭

network-helper01鲜读RF1A20040..1A200AA，29条/106 B两decoder逐字节和边界MATCH。三条件跳出至1A2011D，末条只加载config+18指针；图9个body节点加1外stub/14边，stderr真实ERROR Cannot find function at 0x141a2011d，provider却exit0/complete/未截断。严格检查拒绝把它算完整机制成功，未重跑/跟外边。R30独立核原件；局部读取和callee含义分开，未知不反推拒绝或累计不存在。

| 成本 | Capstone | REA/Rizin |
| --- | ---: | ---: |
| child | 0.419123099 s | 6.2803009 s |
| 峰值B | 24375296 | 1028747264 |
| outer | 2.4258913 s | 8.9567102 s |

INTENT12:16:38.630→close12:43:28.870共1610.240 s；等卡957.370、卡到首child362.136、末terminal到close270.482 s。两受管stage exit0/三MATCH/Job0；不把child6.28 s称完整研究成本。

[关闭/命令/输入/原bytes及独立复核引用](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper01/CASE-CLOSED01.json)；
[完整时间](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper01/TIMELINE01.json)。

## 机制case二：232 B集合，正常本地控制流闭合

network-helper02仅新读126 B，复用已封106 B；合三RF [1A20040,1A20128)，全SHA `91ccef132d8c1a00c34d9723054e6b8b61458408b65c2a8db90774d5a211f6ce`。两decoder64条/字节/边界同；独立正常CFG与Rizin皆20块/31边、14直接跳转在范围内、唯一RET1A20127，无外stub/ERROR，仅保留strings跳过warnings。

五槽皆实读：actor111启用A/B/C可选门，target000跳过三门，均先经常驻root/candidate调用。C恰1才启用附加gate。最终候选+1C0组件非空取qword+308，空时加0；config+20指向累计器，1A20115执行qword ADD。C分支先恢复RSI，共同11 B出口恢复RBX/RSP/RDI并ret。没有正数/饱和/溢出检查，不是checked add。R30独立核验成立；五callee、异常行为、fallback数据、cache lifetime仍未知，不授Army/到场/胜率/CanSend或真实network0可达性。

| 成本 | Capstone | REA/Rizin |
| --- | ---: | ---: |
| child | 0.854972001 s | 15.516943801 s |
| 峰值B | 24813568 | 1038258176 |
| outer | 2.9723226 s | 18.0007699 s |

两stage exit0/三MATCH/Job0。INTENT12:54:14.030→close13:04:17.095共603.065 s；等卡204.970、卡到首child62.958、末terminal到close282.042 s。没有用它与前case作公平提速或token A/B。

[关闭/命令/字节/正常CFG/独立复核引用](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper02/CASE-CLOSED01.json)；
[完整时间](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper02/TIMELINE01.json)。

## 最后workflow：已持Evidence的真实导入、摘要与导出

evidence-reuse01只把上例历史flat Evidence经官方createImmutableEvidenceBundle/serializeEvidenceBundle包为DERIVED容器，同一MCP会话实际import→complete/summary→export→close。原16字段逐值/类型/数组序、ID/parameters/profile=null不变；未打开binary或请求PE/hash/Rizin/Ghidra，不产生新native观察。R38独立读10原件复核，export在client.close之后仍可读。

| 实际返回/结果 | complete | summary |
| --- | ---: | ---: |
| 序列化CallToolResult B | 131281 | 2183 |
| 内层payload JSON UTF8 B | 58734 | 959 |
| client call-wall | 0.0094828 s | 0.0035287 s |

摘要只有身份/来源/retention等metadata，native_dossier为false/different-operation，无raw/normalized/instruction/graph，不能独立回答CFG20/31或+308→config20 ADD；complete/export保留所需原文。字节变小不是等质量token收益，也不是Rizin native dossier分页。

DERIVED输入和实际export各58734 B、字节完全一致，SHA `b169f9ec98c90d3aae021cb753c49ffd173e638e59c1b2d22c254583d1762dc1`。import1条/总1条，unknown0。initialize0.9520024、import8.762849、export0.14732、close_binary0.0039338、client.close0.2579459 s。call-wall包含JSON序列化及RPC归档写入，不是纯server/RPC延迟；未捕捉完整底层SDK JSONRPC流。import慢的原因未定位，不外推固定开销。

单managed child11.131843299 s、峰值693,366,784 B，client报告墙钟10.3418608 s（不含前置模块加载），outer13.3061596 s；exit0/三MATCH/Job0，会话全关闭。active A-INTENT13:31:22.262→close13:49:58.540共1116.278 s，初版未执行proposal起共1427.307 s；等卡376.738、卡到child133.932、末terminal到close594.321 s。卡截止13:49:39，最后close元数据晚19.540 s；实际child在13:40:04.219已结束，不能把整个720 s闭场记为按窗PASS。协调/守卫/解读/独审未各自计时。

[关闭/独立复核/命令及全部原始RPC/导出引用](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/evidence-reuse01/CASE-CLOSED01.json)；
[完整时间](/D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/evidence-reuse01/TIMELINE01.json)。

## resume62 交接边界

没有LLM/tokenizer、受控人工用时或等质量模型token计量。框架源码能力、实际执行、原生局部机制与实机资格分别记录；proper API及Windows入口限制见 [工具页](tools-and-context.md)，方法见 [methodology.md](methodology.md)。

当前0 owned child、0活动MCP会话；不再启动新INTENT/PE/backend/研究，未开始的callee语义留待下次授权。D盘已安装依赖、必要基线和失败原件保留，不清理活跃证据。最后NativeFSI在13:43:46记录tools2,065,350,000 B，case661,160 B加64 KiB收尾预留仍低于4 MiB，output312,592 B低于2 MiB。14:00 UTC为原用途复核点，后继由Root按统一存储策略复核，不自动续执行或删除必要输入。

## resume63：两次新增有限查询

本段前向追加于旧文档提交 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c` 之后。先读框架源码、核23份旧来源，再按每题新问题与容量执行；框架方法见[workflow](resume63-framework-workflow.md)。两题均复用同一已装 REA6.8.0/Rizin0.9.1 与原 PE，没有 PE 副本、callee 跟随、global值读取、unwind body、Ghidra全量导入或游戏启动。新鲜 PE SHA 仍为本页固定输入，imagebase `0x140000000`；版本来源合同不授 loaded 身份。

### Shared 首失败与实际路由

第一题原 `SourceGraphCommandSpecProducer` exit0只生成元数据；`SharedOwnedCommand` 在首child前因历史 accounting pin 的 mutable `STORAGE-SHORT-COMMIT-HEAD-V1.json` 漂移而拒绝，outer4.447 s/exit1，decoder/backend均未启动。见[入口原件与前向记录](resume63-callee1d64290-entry-result.md)。旧失败保留，未获 Shared 资格。

Root 随后明确授权已装官方 `createReverseEngineeringService(...).executeRizinCommand(...)` 正常 direct 入口；使用原装 WindowsOwnedProcess 的限额、exit/close观察与 finally service.close，没有增加 runner 或热改旧runtime。新鲜容量与题目范围仍生效。Rizin 每题只执行一次有界 `af/afij/pdfj/agf json`，没有把 raw Evidence 冒 native dossier。两题输出 complete/exit0/未截断，PE前后身份一致，stderr仅保留大区间strings跳过warning；字节、局部边和实际返回路径另独立校验。

### 230 B：root/candidate gate `1D64290`

新鲜 RF 为 `[1D64290,1D64376)`、unwind RVA `51E6AC0`；230 B、SHA `4aee55a25a91582bad0af6a486f3271ab5d652257f4e0366571fe5e87833d380`。Capstone与Rizin逐48条VA/size/bytes一致，6 CALL与2 JZ的signed displacement独算一致；独立正常CFG为5块6边，唯一RET `1D64375`，无范围外非call边。闭合以六direct和两virtual call正常返回、保留预期nonvolatile寄存器为条件，不覆盖异常/unwind。

entry RDX保存为candidate；entry RCX传给 `B17C70` 构造local context。candidate唯一显式成员读取为 `+18` dword，零扩展写入local qword，另写tag4。`373A0F0` 消费global dword `5D4BFB4` 与local，随后 `1D65640` 返回对象的 `+EF0` 指针加 `1930` 后交 `372DF10`。该call返回的AL经EBX保存，cleanup后 `MOVZX EAX,BL` 原样返回，**没有0/1归一化**。两JZ只控制局部cleanup；该body不直接读 `+308`。自动猜测的stack arguments实际含locals，不作为完整ABI合同。

M5在15:00:07.577Z独立核SHA、48条边界、8个相对目标、5块6边和bundle单record逐值/类型/数组序等价；[DOMAIN-REVIEW01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/DOMAIN-REVIEW01.json>)保留此独审。M2后继另核原bytes与目标算术，未再调用backend。

六direct/两virtual call的完整ABI、语义、副作用、异常、global当前值与领域含义仍UNKNOWN；无兵力、参战、到场或胜率结论。[receipt](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/CASE-RECEIPT01.json>)及[close](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/CASE-CLOSED01.json>)传递引用原bytes、flat Evidence、portable bundle、命令、owned events和复核，不在仓库复制大原数据。

### 119 B：receiver gate `24C5260`

先有限查旧cache/归档，未发现所查位置已有body；这不是全仓不存在的证明。新题新卡只取 RF `[24C5260,24C52D7)`、unwind RVA `5109DB0`；119 B、SHA `f59f55f9bf90ef85fa6b5a603b5f36bffd8ae246a20c23a0283eef784914ebd3`。Capstone与Rizin35条逐字节一致，3 CALL/2条件跳转目标独算一致；4块4边，两RET `24C52C9/24C52D6`，无范围外非call边。

保存entry RCX receiver，`A149D0` 返回对象的 `+F10` qword成key。receiver `+38` begin与 `+44` signed count组成call前end，RCX/RDX/R8分别传begin/end/&localKey给 `A11F60`。call后**重新读取**receiver两字段生成endAfter；`p2=(returnP==endAfter?0:returnP)`。只有p2非零且 `24C3BE0(receiver,key).AL==0` 时AL=1，其余AL=0。两出口仅写AL，不能称整个EAX归一化；也不能假定call前后collection稳定，或仅凭参数形状命名搜索算法。

`native_research_plan.py check` 实际exit0只授结构/文件完整性；`check --for-observation` 实际exit2，正确拒绝offline-only缺少live window/真实producer trigger。没有伪装paused-snapshot；Root另授权的离线文件查询不等于live资格。Rizin `is-pure=true` 保留为自动metadata，不能据此证明三个callee无副作用。

case在15:19:06.718Z闭场时附加M5独审仍PENDING；旧close未改。M5实际复核在15:23:50.518Z通过，15:27:58.546Z另CREATE_NEW [INDEPENDENT-M5-REVIEW01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee24c5260-01/INDEPENDENT-M5-REVIEW01.json>)，7374 B、SHA `d9567d5b65919f108e8f67929db5d4a3a21b1f4ca590bd2cac1cb0e41976e837`，核3份SHA、35条bytes、5目标、4块4边与bundle值等价。三个callee语义/副作用、fallback当前值、异常/unwind及游戏可达性仍UNKNOWN；held caller只支持该AL非零跳过累计。[receipt](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee24c5260-01/CASE-RECEIPT01.json>)和[close](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee24c5260-01/CASE-CLOSED01.json>)保留完整引用。

### 成本、闭场与后继

| 实际范围 | 1D64290 | 24C5260 |
| --- | ---: | ---: |
| 新body / 指令 / 正常CFG块、边 | 230 B / 48 / 5、6 | 119 B / 35 / 4、4 |
| decoder墙钟 / owned峰值 | 0.356 s / NOT_MEASURED | 0.419 s / 24485888 B |
| REA service墙钟 / Rizin owned峰值 | 7.479 s / 592379904 B | 4.243 s / 592695296 B |
| Rizin完整close UTC | 14:56:50.786 | 15:08:48.363 |
| own host/provider PID不在场读回 UTC | 14:59:32.236 | 15:11:43.502 |
| authority T0至case close墙钟 | 848.575 s | 852.596 s |
| case close / deadline UTC | 15:01:16.579 / 15:02:08.004 | 15:19:06.718 / 15:19:54.122 |

Rizin每题provider Job限额1 GiB、未触限；第二题decoder限256 MiB。outer exec session与exit分别留原件，**outer联合峰值/Job0均NOT_MEASURED、Shared资格NOT_GRANTED**。两题service.close无错误，owner children/MCP/exec均0；own PID读回不冒全机器审计。表内service、decoder与完整窗口范围不同，窗口包括协调/源审/守卫/解读/闭场，不能以4–7秒称完整研究成本，更不能据不同题目作提速或模型token比较。

原64 MiB总hold当时前向净分为首case2 MiB、次case16 MiB、未分46 MiB，没有额外64 MiB或物理释放信用。首case后继Native点值545976 B；次case15:11:29Z点值152584 B，均不是历史峰值，close/后继独审另增小metadata。全部原件按统一期限/用途复核；旧900秒卡不续期。后继复用已持103 B `28BFCD0` 与 `A11F60` source-model，Root另授第三题如下。本段没有授Java已采用、完整八M闭合或实机游玩通过。

## resume63：第三题64 B前缀保留PARTIAL

新问题绑定 held caller `1A200C0`：slot3恰1才进入C gate，RCX为 `**config.slot0` root、RDX为candidate；返回AL非零跳过显式累计，否则继续 `28BFCD0` 等门。实际运行时actor/producer trigger及world可达性仍未知，不以静态caller冒live观测。旧 RF 表与所查cache未覆盖 `2B9D260`；不存在的 `shared-function-cache` 目录单列，不算阴性样本。

immutable [PLAN01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/PLAN01.json>)先定义可证伪问题、caller/consumer/trigger与64 B上限。原 `native_research_plan.py` ordinary check实际0，`--for-observation` 实际2，拒绝offline-only缺live window/真实trigger；Root与fresh容量卡另授静态PE查询。准备好plan/check/argv后才启16:05:53.422472Z新窗，work120秒、close60秒，未走已知S26失败入口。

当前 PE `.pdata` 二分无覆盖行，相邻为 `[2B9D1C0,2B9D258,5109D50]` / `[2B9D320,2B9D364,5109614]`。此空隙不证明leaf或函数边界。官方REA raw服务只执行 `b 64; p8 64 @ 0x142b9d260; pDj 64 @ 0x142b9d260`；没有af、callee/branch跟随或新Ghidra导入。64 B raw SHA `257454d4ed0da2768dd07f7869c607fc31988977b8fcf66c87e7f57fa58f1e19`，REA p8与独立原件全同。

前62 B/17条VA、size、bytes在Capstone/Rizin间一致；6条rel8目标从raw独算一致。root/candidate各读 `+1C8` qword：非空则读所指对象 `+80` dword，为空则取 `FFFFFFFF`。两dword任一为该bit pattern即JE至范围外 `2B9D2A2`，否则执行 `CMP ECX,EAX`。字段领域含义不推断。前缀无CALL/RET/内存写，不能外推完整callee无副作用或返回AL。

末2 B `0f94` 从 `2B9D29E` 开始，缺少完整指令。Capstone正确保留undecoded tail；Rizin输出invalid `0f` 后把 `94` 解成XCHG，不能将这两条当真实边界或据此猜SETcc目标/最终AL。两个JMP的ESIL分别写 `0x142c2d279/292`，与raw、disasm、`jump` 的 `0x142b9d279/292` 不同；未用ESIL求证。命令虽exit0/complete/未截断，机制仍 **PARTIAL**。独立前缀图为9块、含两个open stub的13边，外部target `2B9D2A2` 与断指令 `2B9D29E` 未闭；未请求Rizin CFG，不宣称双图一致。

| 实际成本/终态 | 结果 |
| --- | --- |
| decoder墙钟 / owned峰值 / close | 0.377 s / 24805376 B / 16:06:22.345Z |
| REA service墙钟 / Rizin owned峰值 / close | 4.566 s / 592379904 B / 16:06:39.561Z |
| hard limits | decoder20秒/256 MiB；Rizin30秒/1 GiB；Node heap128 MiB |
| 完整authority至close / deadline | 166.238 s；16:08:39.660Z / 16:08:53.422472Z |
| own4PID absence / service.close | 16:07:31.793Z全不存在 / 无错误 |
| outer联合峰值、Job0 / Shared / token | NOT_MEASURED / NOT_GRANTED / NOT_MEASURED |

一次metadata reader在yielded exec尚未终结时提前读Evidence收到ENOENT；随后poll原session9452到真实exit0再读取，没有重跑查询。[receipt](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/CASE-RECEIPT01.json>)、[crosscheck](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/CROSSCHECK01.json>)和[close](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/CASE-CLOSED01.json>)保留真实边界与exact refs；close附加M5独审为PENDING，后继另存原件，不改旧close。

M5在16:11:14.361Z实际独核64 raw、17条62 B、6个signed目标、尾断指令与两处ESIL差异，机械PASS且保PARTIAL；16:13:59.016Z另建 [INDEPENDENT-M5-REVIEW01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-prefix01/INDEPENDENT-M5-REVIEW01.json>)，4972 B、SHA `ebd01b8e2e9a1e45d5bdd36fe01a6cd1e3e9724c71898325a678a67e67907a58`。旧close的PENDING保持不变。

16:09:49Z Native点值为19files/3dirs含root、logical107426 B/native152440 B，非历史峰值；physical release0。新case16 MiB净取原64 MiB未分额，余30 MiB。下一最小问题是断指令与外跳出口的有限后继，必须新问题/范围/预算；本次未扩读，没有Game/Steam动作或新增游戏日。

## resume63：第四题正常AL路径与迟闭场

Root另授新 `[2B9D2A0,2B9D2E0)` 64 B，复用旧64 B，从原entry拼解而非以2A0当entry。新头5 B补出 `SETE AL; RET` 与 `XOR AL,AL; RET`。从entry可达69 B/21条、10块12边、RET2A1/2A4，无call/outedge；后59新增字节padding/邻段不归入此逻辑。正常AL为“两值均非FFFFFFFF且相等”，EAX高位不规范。M5对raw/ModR/M/6个相对目标/可达图独审成立；领域字段、live可达性、ABI/异常/继承链仍UNKNOWN。

Rizin实际p8新64与原件一致；随后 `omj` 在0.9.1不存在，命令列表在RAM128 p8/pDj前停止。exit0/complete不授128双decoder。work截止后未启动修正；闭场长脚本又在exec前被8191本地长度guard拒绝，最小close拆开后实际逾期。decoder0.425 s/24813568 B，REA service4.913 s/Rizin597905408 B；provider16:21:13.898Z及时close，整体case至16:24:41.431Z，共258.399 s、晚78.399 s。outer联合峰值/Job0未测、Shared不授；这是一份预算RED的真实有限字节研究，不能改成整体PASS。

M5另建5614 B独审保留normal-path结论及Rizin/LATE边界，原close的PENDING不改。详见[第四题独立页与全部精确原件](resume63-callee2b9d260-tail-result.md)。四case在原64 MiB净分2+16+16+16 MiB，余14 MiB，无额外hold/release。16:27 Native点值非峰值；16:32:50Z中断恢复后own4PID仍不存在。Root要求不为Rizin形式补测C4，下一问题须另PLAN/实际验证最小close/新卡。

## resume63：M1成员写入的可选前置检查

fresh包含writer2603E46的RF精确为 `[2603AF0,26041D6)` /525FD10。目标原件12 B，实际二分17×12=204 B元数据，非总IO12 B。cache缺完整body后补854+886=1740 B，复用held26；Rizin完整1766 B重读26，单列重复。417条逐VA/size/bytes同，85 signed目标、74块121边独核同；RET41CF与INT3 trap41D5分列，34 opaque calls及异常/unwind仍未知。

M1独审给出正常、不借overflow的局部符号见证：输入byte非零可绕过两个2C7DED0，到append写owner+C/member+8。它仅否定这两个可见call必经，不能证明全局没有验证，也不能命名persistent或join。R15/R13/RBX来源、byte的entryRSP+28位置已追溯，真实caller/byte业务义/自然继承及target重绑仍UNKNOWN。Java成员行继续作为当前观测，不升格成持续资格已执行。

本题先用真实旧closed结果验证短minclose，再按新卡执行；16:50:33.729Z在48.628秒完成owned最小close/四PID不存在，早于16:52:45.101598截止。decoder0.466 s/25341952 B，REA service4.908 s/Rizin592994304 B。后继机械核、M1独审与富metadata不计入48.628秒，研究总用时/token未量测；outer联合峰值/Job0未测，Shared不授。原close payload未分析标记保持不改。

完整字节、原始命令、反例假设、成本与独审见[M1结果页](resume63-m1-member-validity-result.md)。新case8 MiB从原64 MiB净分，余6 MiB；Native点值非峰值/release0。没有新Game/Steam动作或Java字段；后继callee必须另立问题和鲜卡，不续此卡。
### Resume63 C6：2C7DED0 791 B composite pre-append gate

machine_id: `xenoamess-full-tower-eb9d2c1186`。真实caller2C7DF4C所需下一层参数语义见 [完整有限结果](resume63-m1-gate2c7ded0-result.md)。先scoped cache miss，再fresh pdata row153797 `[2C7DED0,2C7E1E7,52B878C]`，17探测行204 metadata B；新791 B/raw `ff4fafaf336cc499bddcdf6b5c186b69eb163a9928e5370b27cfbdebed4cd76d`，Rizin重复791 B单列。Capstone/Rizin197ops同字节，42个direct targets独算一致，36块60边/唯一RET2C7E1E6/16direct+2virtual opaque，无范围外非call。

按既有字段合同，target+40解析后传首2C7D920，member/flags/type/out转参已闭。首P0仅被保留或清零，不归一1；本地flags+2读取发生在首helper之后，不能假定初始五01稳定。输出参数影响短路和下传；不能只当无副作用诊断。RDI保留以正常Win64 callee为前提；join/persistent/loader-slot命名与opaque效果未知。Java无新增领域已知字段或Game资格。

decoder420ms/25272320 B，REA4583ms/Rizin593039360 B；官方service.close正常。先minclose17:25:05.420Z/T0→70.886s，0owned，2091 B/c7bd86d3…保payload未审历史。M1后继独审7913 B/121f9ebc…，富receipt10942 B/a823b23e…在T0后833.929s落盘；整个准备/研究前段未完整计时。outer/joint/Job0未测，ordinaryplan0/for-observation2 offline拒绝；不授Shared/native dossier或加速收益。新850 B题另卡另case，不在C6追加。
### Resume63 C7：Base2C7D920

machine_id: `xenoamess-full-tower-eb9d2c1186`。[独立结果](resume63-m1-base2c7d920-result.md)：新850 B/207 Capstone，Rizin206/849正常可达，尾CC保留；35块57边，20direct/1virtual，RET2C7DC18。known-row只重核12 metadata B；flags3/4令原始Q保留或清0，全部return零扩展byte但不归一1。存在heap/global写，slot-loader/join/persistent未知。

独立新300+60卡，decoder459ms/25325568 B，REA4911ms/592150528 B；先minclose17:45:58.324Z、68.940s/0owned，后review8020 B/fb5f4066…及receipt11073 B/db1a3c24…（T0后909.895s）；总准备研究耗时未完整测量。原close不回填，无backend补测尾CC。outer/joint/Job0未测，不授纯函数/加速/Game资格。

### Resume63 C8: Type2C7E860

[Finite result and exact sources](resume63-m1-type2c7e860-result.md): fresh row12 B, new261 B,59ops/12blocks16edges. type+E5B earlyAL1; first-return+EF0/A90 identity and loader-slot meaning unknown. AL0/1 only; no callee follow. Decoder864ms/25243648 B; REA5474ms/592109568 B. Minimum close18:26:00.903Z,78.256s/0owned; later independent review7160 B/5445e3d0 and receipt11049 B/0c70aa06 at T0+576.739s. Full preparation/research time, outer/joint/Job0 and speed/token benefit unmeasured; no Shared/native dossier/Game credit.

### Resume63 C9

[Local16KiB locator](resume63-m1-inbound2603af0-local-result.md): 16380 complete starts/293E8/0hit; noRF candidate. Minimumclose67.808s; laterM1review separate. LOCAL_NOT_FOUND only, notglobalabsence.
