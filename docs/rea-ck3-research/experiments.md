# REA / CK3 实验记录

machine_id：`xenoamess-full-tower-eb9d2c1186`。本页截至2026-10-26 UTC；完整原件在D盘，来源见 [sources.json](sources.json)。用户已要求收尾：全部会话/受管子进程已关闭，不继续新研究或后台任务。

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

## 交接边界

没有LLM/tokenizer、受控人工用时或等质量模型token计量。框架源码能力、实际执行、原生局部机制与实机资格分别记录；proper API及Windows入口限制见 [工具页](tools-and-context.md)，方法见 [methodology.md](methodology.md)。

当前0 owned child、0活动MCP会话；不再启动新INTENT/PE/backend/研究，未开始的callee语义留待下次授权。D盘已安装依赖、必要基线和失败原件保留，不清理活跃证据。最后NativeFSI在13:43:46记录tools2,065,350,000 B，case661,160 B加64 KiB收尾预留仍低于4 MiB，output312,592 B低于2 MiB。14:00 UTC为原用途复核点，后继由Root按统一存储策略复核，不自动续执行或删除必要输入。
