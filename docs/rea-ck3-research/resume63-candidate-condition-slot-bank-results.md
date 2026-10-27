# Resume63 候选、条件、receiver 与 bank 来源

观察机器 `xenoamess-full-tower-eb9d2c1186`；2026-10-27 UTC。静态研究不新增编译、当前帧发布、自然事件、Game、SAVE/RESTORE或动作信用。原始失败与回执保持历史身份。

共同输入：CK3 1.20.0.4/build25734779，PE101040248B，SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。路径以 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/` 为根；目录别名仅导航，文件以bytes/SHA256引用。

## M1：候选返回生产者推进两跳

A=`resume63-m1-candidate2929de0-01`；B=`resume63-m1-q28fdbb0-01`。

919B/240条、67块109边逐原字节、Capstone、REA pDj/p8/CFG独核。所有正常返回的 Q 来自 CALL28FDBB0，非已证“现有 heir 容器选择”；该调用支配唯一正常 RET。R10 在初读全局后跨 opaque 调用，不能追认为原 registry。entryR8 传给 producer，随后重读其 DWORD 也不能追认为调用前值。

376B/92条、12块17边把 Q 来源进一步闭到 CALL28F3470.RAX→RSI→正常返回 RAX。entryRCX=M，entryRDX=D，entryR8D=K，entryR9=X，另有入口第5/6/7参数；初次 producer 显式接 M/P，其余易失参数未重设。首个28F36E0只写R9B=1；末次写R9D=0，不能混成完整布尔合同。条件路径可将 Q+40 交 opaque855DB0；副作用、Q非空、创建/已有身份均未闭。另保留 DD22 CALL4232A70→DD27 INT3；DC73合法自环不被 AF loops0 抹去。

下一边是 **28F3470 返回来源**，先held/RF定位再另授有限体；B=entryV+140 的32B companion填充仍无写入seed，保持 B_FILL=NEEDS_LOCATOR。actor/frame/cohort 自然触发与真实新 append 未证，不能给旧 episode risk/member 续权。现有 FactionRead 与 cache-clear 发布边界继续保 UNKNOWN；本轮无 Java 行为改动。

## M2：真实 mode0 过滤与终验

C=`resume63-m2-classifier372e000-01`，完整RF1070B/269条。Capstone重组全raw，官方p8全同，原signed边及48块71边与agf一致；官方仅 afij/p8/agf，**没有 pDj，不能称第二套逐指令解码**。两处NUL诊断扫描自环与 AF loops0 不符，不授多条件次序。

entryRCX是条件receiver，entryRDX是**整个context**。WORD0仅绕过非零tag的registry validator，仍须 opaque372B4C0通过。372B4C0接 receiver 与 [context]；随后虚表+C8接 receiver 与整个context。C8原AL按0..255返回，未归一为bool；首失败仅清AL，高EAX未知。incomingR8B控制失败诊断，不是hidden/disabled分类，也不表示NULL；跨opaque后R8未知。没有NULL守卫、空列表恒真、顺序或execute证明，不能当纯getter反复调用。

372B4C0的same-PE144B旧原件已有，避免新采；真正缺口为 **当前同帧 option+80/+150→vptr→slot58/60/C8 的typed target locator**。现有EventWindowCodec/EventPolicies仍以native实际rows/index为动作authority；不得重建脚本谓词、硬编码4/8或授三自然事件信用。

## M5：slot反证与receiver中转

D=`resume63-m5-vtable-slot488fe20-01`；E=`resume63-m5-vtable-target2e1ae80-01`。

publisher旧230B给初始U.vptr=VA14488FE18。实际DATA8 slot+8字节 `80aee14201000000`，LE64=VA142E1AE80，**不是VA1431C7680**；官方derivedraw p8交核，code/RF/UW读取均0。此反证仅针对初始表的直接槽假设，不能证明跨opaque后freshG==U或vptr稳定。

新RF49B/16条两decoder+p8一致。entryRCX=O保存RBX；先直接CALL2E40CC0(O)，再fresh[O]取vptr、RCX=O调用[vptr+38]。freshDWORD[O+48]非零（不是“正数”）则RET保留虚调用原RAX；零则RCX=O+38并tail9D0A00，其返回未知。object+38与vptr+38不是同一地址意义。3local块及1外stub/3边保留，外tail无body。stderr484B含四条strings警告及 Cannot find function；exit0不能掩盖。原ESIL误写1409E0A00，raw/Cap/opcode/jump为1409D0A00，拒采错误ESIL及purity/loops推断。

下一强seed是 **第一次直接2E40CC0(O)**，优于假设vptr稳定后追初始+38；须另授最小范围。无直接31C7680不排transitive注册。registration owner/getter receiver别名、loaded DB/default及war合法性仍未闭；现有C2/F10与WarEntry消费者不据此增DTO、自动宣战或金额资格。

## M6：owner/vector地址与getter快照

F=`resume63-m6-batch-owner-vector-prefix140-01`。140B/34条仅入口prefix，非476B完整RF。Ctl=entryRCX；[Ctl+18]在getter前保存为calleeRCX；entryEDX低32位传R8D；getter后读取signed DWORD[Ctl+10]。真实19E82A7 CALL1A2B9C0的RDX为 Greturn+24×(signextended slot+BAh)，模2^64。负值/≥7进opaque3F7AB70，若返回仍fallthrough，不能假定noreturn。prefix无RET，两个窗外出口保持UNKNOWN。

已持89DA60完整87B/18条经旧decode/raw重新逐字核，0新PE/provider/decoder：Greturn是89DA64首读全局5C67538，或零路径opaque3F8B640正常返回后89DAAB重读的QWORD快照。**不是使用时刻再读global**；可为零，无本体global store，不授纯函数/无参ABI。旧来源machine_id unknown，仅静态复用。

下一缺口为 **5C67538实际writer/typed loader 或 Ctl+10/+18 producer**；诊断helper不是正向加载seed。现有OrdinarySwaySchedule root frontier与NativeInteractionAi prepared-row路径不等于fullbank/fullID producer，不能据地址公式发布Known或新增策略。

## 精确终态与同行来源

以下SHA256均完整；M3/M0同行是带时间RAM消息，不伪造为文件。owner receipt中PENDING不倒填。

| 别名 | owner原件 bytes / SHA256 | 独立peer bytes / SHA256 |
| --- | --- | --- |
| A | CASE-RECEIPT01.json 5081 / e4e384a1993bedce0d7378391d454d0a5ed3884e600d0b4991e94a7c9e125f8c | INDEPENDENT-REA63-REVIEW01.json 4246 / b327d89959b1b0af28916d591fdec33aa6cc3298720d4858f965aeaf30a2dccf |
| B | CASE-RECEIPT01.json 6009 / 3f9bed257a67bcbe8ca01492edf33cb8e0167eb87e33f12be102368baa264b98 | INDEPENDENT-REA63-REVIEW01.json 4294 / 3456c5964277687e3ccb1f5f9de78ea4b47d040bb8f1709cdbde50f7e1accd2f |
| C | CASE-RECEIPT01.json 10308 / 02fea0eac1955fe4b54383224251af9bf2c15e75e86788c1cce694b57b469be8 | /root/m3_rea63 RAM 08:18:55.941Z；08:21成本与context澄清 |
| D | CASE-RECEIPT01.json 6482 / c34a2569dc158d8f79236fe6e848bb94b3dde460dca8344e2df9449650a9d319 | INDEPENDENT-REA63-REVIEW01.json 3673 / fee30c24acc5ff9a07641df93e0c86195fbc83e9c01ff213ec12b3f69a075c03 |
| E | CASE-RECEIPT01.json 8068 / 317da91f63b0d59221b66b20f0fbeae2703b593d339ccaefc1c933963f49bf11 | INDEPENDENT-REA63-REVIEW01.json 4030 / e59b2388fe16df3bb1b29c5bc4fa26581e564953719037f7485c04c904d805e5 |
| F | SOURCE-NOTE01.json 6793 / 579c17447719924a0a998f8a3d2d5bc775a596243dfb24cafc7128770799e277 | /root/m0_rea63 RAM 08:06:34.376Z；08:39:41.549Z成本澄清 |

87B原件：`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-0089DA60-0089DAB7.bin`，87B/SHA256 `9f6d50a843453c530476fe2e250eb322377244bac691d5f5ce8d6db4ac77ac6c`。DETAIL18条与raw相等；非fresh取证。

## 成本与结论边界

六case均先最小close、按窗owned0；A/B原active_exec UNKNOWN保留。Rizin wrapper毫秒依次A239/B167/C4373/D158/E4780/F189；13个Owned wrapper墙钟合13.208s、6个Rizin合9.906s。实际child/Rizin最大并发均1；首卡07:55:33.863至末close08:51:57.546为3383.683s，包含间隔/分析但不含全部准备/后续peer，不能冒整体提速。

所选code/data2562B不等于I/O。capture源码口径：A202081427、B202080884、C101041878、D202080504、E202080557、F101040400逻辑B；C/F各一次PE SHA，其余双SHA。C/E官方原PE的SDK前后digest按当前实现与保留字段另计404160992B，合1414566642B，**source-derived，非历史pass计数器实测**；排除backend额外读、held metadata及derivedraw I/O。物理I/O、outer OS Job与joint峰未测，阶段峰不相加作joint实测。

B的MOVUPS raw方向证stack store，不能照Cap accessbits误标只读；unsafe Rizin整数保持词法、不经Number，错误ESIL/自动purity/loops不授信。B卡外发expectedSHA未在launch前独立硬比，close后card/EX精确MATCH；保此边界，不补写旧守卫。静态研究不替代现场后态。
