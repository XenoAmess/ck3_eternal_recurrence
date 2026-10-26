# resume62 收尾交接：Java / G2 / REA

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26 UTC 收尾，14:22Z 汇总最后序列化结果；本次重新执行 `py tools/ck3_live_run_id.py machine` 核实身份。精确原件路径、大小和 SHA 见[机器可读索引](2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)。

## 接手先读

用户要求同时开发自动游玩智能体、G2 的 M0–M7 和原生机制研究，工作期间目标为 60 个有具体任务的工作智能体；全部保持当前模型，容量不足持续重试，不改用其他模型。随后明确要求深入研究 REA，研究采用 REA 或同类证据方法，并实时维护专门文档目录。

最新指令是“你要去度假了，收尾手上的工作，梳理交接文档到 docs”。已停止派发研究、补并发和启动构建/实验/设置。恢复时先核本交接及实际文件，不重放过期卡或假定原智能体内存仍可用。

- 本轮 CK3 启动、游戏新增日、实机 SAVE/RESTORE 均为 **0**；Java G2 八 M 完整实机为 **0/8**。
- Host、Native、Acceptance、SDK、Readiness、Runtime、REA 执行岗均报告受管 child/session/Job 为 0。Host 于 `13:50:01.8647776Z` 对原构建锁排他打开后立即释放，并核指定构建进程集合为空。此结论不覆盖整机未知进程，也不表示整机没有 CK3。
- **最新 Tools 完整验收仍失败**；最新局部 8 类 67/67 通过不能替代完整验收。SERVICE、SDK 原 30 step、Application/NativePlan/Definitions/Core/Game 尚未完成。
- 可复用开发源码、BUILD、m2、TMP 和真实失败全部保留。没有提交、推送或清理工作树；i61 投影并非完整最新源码。
- 最后团队清点中，除 R26 因模型容量不足保留 errored 外，其他子智能体均已 completed；没有为收尾重启 R26、切换模型或补足60并发。最后几次命令仅保存既成资料，均已终结。

旧入口保留：[resume61 原交接](2026-10-26-java-g2-resume61-runtime-priority-handoff.md)、[原索引](2026-10-26-java-g2-resume61-runtime-priority-source-index.json)。[当前日报](../autonomous-agent-progress/2026-10-26-java-g2-resume61-current.md)及[验收矩阵](../autonomous-agent-progress/2026-10-26-g2-resume61-acceptance-resumed.md)部分早于最后终态；发生冲突时以本交接和实际回执为准。

## 工作目录和执行规则

| 名称 | 实际路径 |
| --- | --- |
| 仓库 | `Z:/ck3_mod_rewrite` |
| B | `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025` |
| O，Host 控制/回执 | `B/resume61/host_integration` |
| SRC，可复用 Java 开发源码 | `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control` |
| WORK | `D:/codex-ck3-demos/2026-10-22-java-phase1` |
| BUILD | `WORK/build/complete35-candidate31-h5r5` |
| Maven 缓存 / TMP | `WORK/m2` / `WORK/scratch/complete35-candidate31-h5r5-tmp` |
| Native 冻结源 / 可复用构建 | `B/native10/dev61/ck3_autonomous_player/native_bridge` / `B/native10/build61/dev` |
| NS，Native 状态 | `D:/ck3-state/ck3-java-g2-r5-native61` |
| G2，软件回归 | `D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04` |
| STATE，首场输入 | `D:/ck3-state/ck3-java-g2-robert1066-resume61` |
| REA 工具与原件 | `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01` |
| 唯一交付树 | `D:/codex-ck3-background/i61` |

路径缩写只用于阅读，执行时展开。Host 为 Java SRC/BUILD 唯一 writer；Native 为共享 helper/test 唯一 writer；Delivery 为 i61 唯一 writer。不要在冻结 Source15、S26、SDK/runtime 中热改。

默认命令行 `mvn` 实测为 3.10.0；74 报告 home `C:/apache-maven`，JDK 为已有 `C:/jdk-21` Temurin 21.0.10+7。这是本机事实，不在后续命令中锁安装路径。已知编译失败继续同 SRC/BUILD/m2/TMP，用模块选择及 `-T2` 增量修复；局部和必要测试通过后再一次完整验收。

**禁止 PowerShell。** 使用 `cmd.exe`，复杂脚本经 base64 传给 Node/Python。曾有裸 shell 重定向把 Java 文件截空，已精确恢复；不要把 `->`、尖括号或多行代码未经编码交给 cmd。新生产/构建/编排代码使用 Java + Maven + Quarkus；本次 helper 是既有低层 Win32 Python 的维护。

## Java：最新失败、已采用内容与下一步

### Tools74 的真实阻塞

`O/TOOLS74-FULL-VERIFY-ACTUAL-RESULT-CLOSE01.json` 记录：

- inner Maven exit 1，55.730140101 秒；outer Shared exit 1，125.042706 秒；Job0，三项守卫及 source/compiledSource MATCH。
- 默认 Maven 3.10 明确拒绝 `maven.config` 中的目标：`Unrecognized maven.config file entries: [verify]`。
- **未进入编译/JUnit，complete deployment 为 0**。原失败快照、参数、日志和回执保留。

原因位于共享 `MavenArgumentFile` 的真实执行合同。typed Lobby 使完整 argv 经 manifest/config 路径传递；软件 67 项没有覆盖默认 Maven 的 config 解析。不能删除 guard、手改74快照，或把普通 Jar 当作 completed。

SDK 已完成两叶候选：v2 manifest 保留完整 original argv，config 只放 `-D` 属性，其余选项/成对值/目标按原顺序走 CLI；历史 v1 严格读取保留。原6+4操作已保存至 `G2/controls/handover62/ram-ops/SDK-MAVEN-ARGS-RAMOPS01.json`，11551B，SHA `f25ef9f7c90c4228700d32b434cc93564fe478ed08b6d7de2df0daaa92650371`。候选尚未采用、编译或运行。先核实际前像再采用；必要回归应包含实际默认 `mvn` 对最小离线 POM 的调用，随后再完整 Tools VERIFY。

### 当前稳定物与实际编译范围

- 77 稳定普通 Tools Jar 为 `BUILD/ck3-control-build-tools/ck3-control-build-tools-0.1.0-SNAPSHOT.jar`，3355911B，SHA `a3d12c732f37f46c9eb0ba89fc2d084b3a415671e02ff0e5e9a3d0724d51341a`；lib5 与 1386 个 main entries 已核。它没有 completed 资格。
- `TOOLS74-SOURCE-CHOICE02.json` 有 324 个 source pins，相对65仅7个批准差异：ControlBuild、ControlCi、MavenArgumentFile 及4个对应测试叶。后继 SDK 修复不能追记到这个旧选择中。
- R33 package pending allocation 三叶已采用。76 实际只重编 **2 main + 1 test**，19.066 秒通过；77包装没有重编。新普通 Jar 的原8整类 **67/67 PASS**，Job0、三 MATCH、62 after pins MATCH。
- R33 以 package-private typed allocation 区分 package 剩余总额与原16MiB metadata 合同；原 metadata 限制不变。不能改成传0、clamp16MiB或混用 total。
- 65 的旧完整 VERIFY 为1054测试/4失败；SDK夹具、真实 Lobby 输入和旧容量断言已修并局部验证，但74在更早的 Maven config 入口失败，尚无后继完整测试通过。

### LS 编译仍未完成

73 使用局部诊断 profile，实际 javac argv 含 `-XDshould-stop.ifError=FLOW`，保 lint/Werror；一次显出10叶14个 checked 错误。75已真实采用这10叶，但后继180秒 accounting 超期：outer191.084秒/exit1/Job0，inner Maven exit、sourcePostcheck、actual receipt 缺失，状态 **RED_INCOMPLETE**。日志 LS579 test sources、0 printed error不等于LS编译通过。

后继恢复600秒 inner、720秒 Shared及180秒 close预算；不要用错误时快速退出的39秒推算成功生成大量 class 的耗时。最终完整 VERIFY 不带诊断 profile。LS POM 已实际选 `finite-first-live`，其配对测试已采用；不要全局替换其他 public host 的名称。

## M3 / M0：准确失败范围

M3 NativePlan 原整类5/5软件测试通过。NT拆组6/6通过，已投i61对应单叶。Restore20先前夹具非法日期/输入合同已修，但不是恢复整图通过。

最新 q10：诊断单叶实际采用，AWIF 为99406B，SHA `4fd9b2a6a47b615d64ec3cf03126d834f799602f0b49afe8c2d145bcb7edb0c8`。strict1 编译通过后，原 LS5 **5 found/started、0 PASS、5 FAIL**；270.8796195秒/exit1/Job0/三 MATCH/261 after pins MATCH，非超时未知。

- 4项真实 typed reason 为 frozen observation/deadline 在 planning publication 前过期。
- 1项为 planning reads 期间过期。
- 具体耗时来源仍未定位，20秒 deadline、30秒 validity未放宽。Comp9 和最终 whole20 未执行。

原AWIF嵌套 QUERY 同时承担 borrowed-writer 自测。M3提出物理fixture分域方向仅为待审建议；间接 `lastNestedRead` 依赖未核完，**没有批准跳断言或删除嵌套读取**。先沿真实失败分支定位，不再次盲跑同输入。

M0 Cold17：合法日期隔离源已采用，strict5编译15 classes通过；原17运行180.210251001秒超时/exit124/Job0，JUnit计数全部UNKNOWN，不能记17 FAIL。没有诊断栈；不要直接再烧旧 Jar62 的长跑。

## Native / Defender：构建通过，登记未完成

Source15为冻结accepted源；原95整组测试已通过。ENV22已通过并闭场；BUILD24沿同 Source15/S26/ENV22/scratch22/cache 通过：request35.290秒、execute374.987秒，均exit0/Job0/三 MATCH。实际 **1 CXX identity 源 + 1 DLL link**，injector未重编；不能称no-work，也没有整图重编。

当前共享 `tools/register_project_exe_exclusions.py` 与原测试叶已经实际采用：helper32965B/`219fd7cb…`，test37485B/`c5ad86df…`。新增11个方法全部 **NOT_RUN**，类型检查 **NOT_RUN**；此前“仅RAM”已被这次采用取代。原低层WMI维护增加same-admin三数组、实际PID/SID及每次Add后读回；不得用普通token空数组或额外JSON字段冒充已验证设置。完整源码delta在 `NATIVE61-HELPER23-SOURCE-ONLY-HANDOFF01.json`。

本机固定 `C:/Program Files/XAR CK3 Project EXE Broker` 缺失，REGISTER21真实失败于broker-dispatch，未调用Add/未弹UAC。历史其他机器broker事实不能借用。D根有普通principal可替换祖先的权限，原安全检查不接受；**未改D全卷ACL、未部署不可信持久SYSTEM代码**。

选择现有 Java `NativeProjectExeUac` 演进一次性登记：新current-plan限定本次唯一injector、实际source/build，单runas进入同类受限admin-child，先验actual elevated TokenUser为本次owner，再执行原S26 Shared完整REGISTER；不外部Add后导入回执。旧两target API保留。R34已将完整119933B RAM ops持久化至 `NS/controls/uac-current23/UAC-CURRENT23-JAVA-RAMOPS01.json`；**未全稿独审、未采用、未编测、未UAC**。

恢复顺序：原helper完整软件回归与修改范围类型检查 → R34完整独审/必要真实consumer与回归 → 新helper对应fresh runtime inventory → 完整可审计划及原受管REGISTER。旧REGISTER21 stage已消费且失败，不重放；本轮没有新增UAC、设置写入或Game。

可复用静态工具：`D:/ck3-state/ck3-java-g2-r4-dependency-setup53/test-venv54/Scripts/python.exe -I -B -m mypy`，已读出mypy1.15.0；缓存显式放获准D根。未实际运行类型检查，不必为找不到本岗venv工具而重复安装。

## 首场输入：Genesis真实生成，执行接点仍待实现

实际 runtime census 仅覆盖声明的 ledger 空根，1333B COMPLETE、0 files/1 dir/4096B；不是全项目或完整Runtime库存。随后 Genesis CREATE_NEW 及 Native readback真实通过：anchor、snapshot各719B，同内容SHA `c8a1451e…`，NativeFileID不同，sequence0、awaiting_initial_entry。

**不得再次初始化。** 下一进程要针对写后真实状态重新 Census，实际纳入 artifactRoot、ledger、incidentBase、scanBase，再取得同窗口完整authority。App用snapshot路径与实际anchor ExactRef。旧13Z census/lease已过时；新窗口没有真实同窗口前头时使用generation1/null，旧claim算other，不能把旧ledger直接冒gen2。

历史11DATA/10角色及剩余12依赖索引保留。genuine SERVICE、Application/NativePlan/Definitions/Core/Game尚未产；旧Sway不重放，不循环重新生成全部初始数据。

已纠正“全repo循环”推断：NativePlan真实main及Profile/Formal/Original直接Command有独立Guard发布入口，不直接要求completedSERVICE；SERVICE要求在受管stdio Session路由。具体缺边是直接Command同Prepared发quote后等待stdin binding，而Shared普通Windows子进程stdin=NUL。

Root批准的最小方向：**现有Command/Protocol增加严格typed FILE_REPLY输入**，同child保同Prepared，仅替binding来源。实际outer请求、canonical quote原件/摘要、phase/order、目录Native身份、deadline全部关联；只接独立issuer实际Binding，仍走原Guard/create/readback。不得伪造Session PID/nonce/WriteReceipt，不放松SERVICE/mandatorytests。此方案仅RAM、没有完整ops、没有源码或执行信用。ENV observed写进payload，NormalExit私有Projection不可在guard创建后重project，不能简单拆成多进程fresh prepare。

另一个必要待实现接点由M1持有：Root Runtime Launch准备器的TMP/env/日志布局与Shared注入不兼容。已批准在原入口增加受限RootInvocation/v5、单一Shared提交、实际额外runtime classpath授权及 `SharedCommandOutputReader` v5分支（共至少5个真实consumer叶）。旧v2/3/4、UTF8、MSVC、native reader保留；不能手删argv或绕过日志/来源守卫。收尾已保存 `M1-ROOT-LAUNCHER-PARTIAL01.json`：仅JRL9操作及SourceGraph1个草稿操作，**Shared/LS/Reader及测试尚未实现**；完整候选尚未独审/采用/编测。

## REA：专门知识库与已验证结论

入口为[REA研究目录](../rea-ck3-research/README.md)，含方法、学习日志、实验、工具矩阵及精确来源索引。六文件实时维护已经建立；原始证据与依赖在D盘。Node24.22.1、REA6.8.0、Rizin0.9.1、Ghidra12.1.4，发布commit与main分记，无全局PATH/TEMP改动。

- 同Rizin命令两组冷对照：direct5.328/4.601秒，REA8.936/6.438秒。没有整体提速或token节省结论。
- Ghidra Windows辅助JVM堆问题经D隔离启动脚本七处最小补丁后实际进入全PE分析，仍在900秒provider启动预算失败；没有成功pseudo、warm或native dossier分页。标LOCAL_PATCHED。
- 106B RF有29条指令但出界；前向补126B后232B/64条、20块31边在opaque call正常返回条件下本地闭合，局部把candidate组件+0x308加到config+0x20指向的累计量。5个callee、unwind、缓存刷新、到场/胜率未知，不授实机或完整业务语义。
- 五callee规划已由M2汇总：1D64290 RF230B尚无body；2BAA6F0 RF91B已有旧asm可复用；2B9D260、28BFCD0无表内精确/覆盖RF；24C5260 RF119B尚无body。旧RF/历史freeze machine unknown，不倒填当前机器；这些没有新采样。
- 最后Node-only实际import/export复用了历史证据：完整/摘要CallToolResult131281/2183B，但摘要没有CFG/ADD答案；只证导航与保留，不能称等质量token节省。DERIVED与export各58734B同SHA，close后仍可读。child11.132秒/Job0；**close元数据晚卡19.540秒**，不能记全720秒闭场按窗PASS。

后继采用问题→版本/字节→有限查询→独立核验→结论/UNKNOWN/成本及原件引用。会话证据ID不自动持久，先导出完整parent；内部hash自洽不替外部PE绑定；exit0/complete不替命令语义成功。模型token仍未计量。

## i61 与后排候选

i61 detached HEAD `b8ddb3901f5648c3881299fd0b72a2a4d3636309`，仅60 unique源码叶投影，NT6是其中单叶更新。`I61-SOURCEGRAPH-OWNER-NAV11.json`只覆盖63–70的148target归属；后续157target链仅RAM，不冒完整现图。

三个NT→LS测试迁移尚未投；不要按basename误删另一个adapters-storage同名类。resolver先验带old/new完整selection再relocate，最后过滤old；原owner map的from/to别名不是typed relocation authority。

COMMON最终图需保literal baseline FileRef，更新实际唯一POM winner。i61 `application.properties`477B保留用户已有dev instrumentation配置，不能用SRC363B覆盖删掉；8个仅尾LF差异不做全树normalize。

四个零JUnit `*Test` helper已批准在最终clean/source capture边界改名，旧79951B ops包是历史候选，AWIF前像已漂移。56叶182替换须重新核；完整CI未跑。LS test main仍是TEST角色，现SourceGraph FileRef拒绝直接test-classes目录；标准test-jar POM方向仅RAM，没有真实新artifact/inventory/命令资格。

收尾按原G2预算仅序列化已经存在的候选；没有借此新开发、编译或研究。下表文件均在 `G2/controls/handover62/ram-ops/`，完整路径及SHA在索引。文件名保留RAMOPS历史称谓，不表示现在仍无文件；其中旧 `RAM_ONLY` 状态描述生成时事实，不能覆盖这次实际保存事实，也不能授予源码采用信用。

| 文件 | 实际字节 | 可恢复范围与限制 |
| --- | ---: | --- |
| `SDK-MAVEN-ARGS-RAMOPS01.json` | 11551 | 两叶6+4操作；未采用/编译/运行 |
| `M0-CANDIDATES-PARTIAL01.json` | 17870 | 两组完整操作及R01/R24导航；其他body缺失 |
| `M1-ROOT-LAUNCHER-PARTIAL01.json` | 38924 | JRL及SourceGraph草稿；真实其余consumer与测试未实现 |
| `M4-CASH-RAMOPS01.json` | 43152 | 原五叶22操作原样保存；不含晚ROOT新包，历史前像未重验 |
| `M5-CANDIDATES-PARTIAL01.json` | 108048 | date05操作及部分正文；app04 donor仍外部，Sway/related/r30仅导航 |
| `EVENTS36-41-RAMOPS01.json` | 91563 | 八叶27操作；排除30/31，35已被后继替代 |
| `M6-CANDIDATES-PARTIAL01.json` | 50698 | Core部分操作及R27路由数组；R26/HALT/MOVE08/Contact等仅导航 |
| `M7-CAP-RAMOPS01.json` | 34875 | 四叶20操作与设计说明；未采用/编译/运行 |

独立源审不等于已采用；partial不是完整恢复包。R14八叶481523B、R26及其他未交出原body的候选仍只是会话RAM或导航，不保证跨会话可恢复。原本已采用的P0在各包中单列，不能把整个包记为已采用。恢复不要一次夹带所有候选进入首场cut。

## 恢复优先级与保留

1. 核本机、路径、保留项和新鲜容量。旧卡及过期review不重用；不恢复60席空等。确认执行owner/原锁后，先解决真实Maven config拒绝，跑必要实际入口回归，再完整Tools验收及原SDK30step（含独立Python continuation）。
2. 同原开发目录继续LS增量编译，消费真实诊断；M3先定位q10已证过期路径，不放TTL、不跳nested断言。最后一次完整编译验收必须真实完成。
3. 并行完成helper回归/类型检查及R34独审；fresh inventory、实际管理员登记后读回，不把UAC ACK当成功。
4. 完成同Prepared FILE_REPLY和RootInvocation/v5的真实producer→全部consumer闭环；取得actual剩余DATA、SERVICE/packaged入口和完整权威。
5. 真正启动前后台刷新Steam offline原生回执，核机器/版本/出生时间和现CK3进程ownership。旧offline不授资格，不抢焦点、不截图、不自动联网或终止未知游戏进程。Java/HTTP/ACK/编译均不替实机结果。

容量与期限统一服从[存储策略](../storage-retention-policy.md)及[版本参数](../storage-retention-policy.json)。本交接两个文件峰值96KiB已获净额预算，REA知识库峰值64KiB另保留；RAM保存峰值8MiB包含在原G2 96MiB内，未加总hold，没有新C盘bulk。Capacity最终记录财务180，D/Z实际可用均高于各自预留要求，但那是记录时事实，不授下一轮容量资格。

可复用工作树/缓存、当前初始账本、已装REA依赖及未解问题的代表性失败仅作静态必要基线保护，最迟 **2026-11-02T14:11:19Z** 复核，恢复或解除引用更早发生时提前复核；不自动续期、删除或授新执行权限。旧hold没有因停工擅自释放，Native7GiB全域actual和whole `.git` physical仍UNKNOWN，不能报告为空或已释放。

旧SDK Config01与旧大派生patch已依法精确回收，原路径不可读，保小receipt/recipe。不要按旧名字制造替代原件。新交接/索引和已封SOURCE_ONLY候选是接手入口；旧失败和历史索引保持原身份。
