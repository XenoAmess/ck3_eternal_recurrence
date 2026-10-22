# M7 Java 构建交接（停止状态）

- machine_id: `xenoamess-full-tower-eb9d2c1186`
- observed_at_utc: `2026-10-22T15:03:29Z`（实际 clock）
- owner: `/root/g2_m7`
- 用户休假交接指令已由 Root 转达：不再启动新作业或 java11；不继续源码修改/编译。本文件写完即结束。
- **java11 未启动、无 session、无 actual receipt。** 已准备的历史命令只到 JAVA10；不得直接重跑已有 attempt 名。

## 最后实际进程与证据

`java10`，工具 session `4965`，已实际消费终态 `exit_code=1`。正式执行入口是已资格化 tools20 的 `ControlBuild`，默认 `call mvn`（实际 3.10.0；最低稳定版本 >=3.10.0，不锁安装路径）、完整 `verify --fail-at-end`。

- 终态 UTC：`2026-10-22T14:57:09.049000900Z`。
- 原生受管根：cmd.exe PID `233036`，FILETIME 十进制字符串 `134371545419048556`。
- Maven：79.1323476 秒，exit1，stop_reason=null，Job active=0，峰值 1,149,415,424 B，硬帽 2,147,483,648 B。
- 编译快照 postcheck=`MATCH`；原 Z 源 postcheck=`MISMATCH`。后者不能追认为当前源已通过。
- 回执 `J/logs/build-java10.json`：336483 B，SHA256 `05adc116a9f40c644cd007174252e6a81b1ad7f0c4a854d203de3c2817f01883`。
- 完整 Maven 输出：`J/logs/build-java10-verify.stdout.log`、`.stderr.log`；外层命令及输出：`CONTROL-BUILD-JAVA10.cmd/.stdout.log/.stderr.log`。
- 原始源及编译源逐文件 pins 均在回执 `source_pins`、`compiled_source_pins`，编译树 `J/scratch/source-java10`。
- `J` = `D:/codex-ck3-demos/2026-10-22-java-phase1`。

所有 M7 启动的 Maven/辅助 Java 进程均已自然终态，无 M7 inflight Job。此陈述不替代 Root/storage/CI 各 owner 对其他并行 capture、Python 检查或 SDK 进程的终态确认。

## 当前父图 17 模块与 java10 实际执行范围

父 POM 已实际读取为下表 17 模块；Root 独占注册/Git/index。本交接没有执行 Git 操作。

| 模块 | java10 实际结果（只对应其不可变编译快照） |
|---|---|
| contracts | 15 tests PASS，0失败/错误/跳过 |
| local-service | 编译及 fast-jar 构建完成；无本模块测试；整图 RED，不授正式部署资格 |
| native-diagnostics | 16 tests PASS |
| war-policy | 71 tests PASS |
| campaign-score | 73 tests PASS（含 ScoreDecimal 三方法仅 public 的本次快照） |
| finance-policy | 132 tests PASS |
| event-policy | 42 tests PASS |
| military-policy | 82 tests PASS |
| late-outcome-reconciliation | 27 tests PASS |
| governance-policy | 132 tests PASS（教育14、crown29、heir10、lifestyle62、perks8、marriage9） |
| planning-runtime | 49 run /0失败/1错误/0跳过；optional mandatory golden 缺，其他四叶及 optional 其余15通过 |
| closed-failure-recovery | 11 tests PASS（anchor 映射及 raw-token 负例修后） |
| admission-contracts | main 编译 RED：FullBatchTiming.java:271 的 deprecated JsonNode.fields() 遇 -Werror；尚未运行 JUnit |
| replenishment-policy | 8 tests PASS，已实际消费 replenishment05 mandatory golden |
| wave2-military | 全部 main/test 编译完成；393 run /84失败/89错误/0跳过（220通过），大量 mandatory golden 尚缺；须逐报告区分真实缺陷与缺资源 |
| build-tools | 23 tests PASS（全五个 suite） |
| wave2-runtime | 因 admission-contracts 编译失败，Maven SKIPPED，**未编译/未测** |

总计实际 1074 tests /84 failures /90 errors /0 test skips，900通过；runtime 的 Maven SKIPPED 单列为未执行。整图 RED，不能报告17模块完成。其他 wave2/3 家族未注册，未被本轮 Maven 验收。

各模块原始 Surefire：`J/build/java10/<artifactId>/surefire-reports`。Root/军事域 lead 已接收393项原始报告，负责分给现有 owner；不为缺样本删测试或计 skip 通过。

## 已完成工具资格及历史 HTTP 闭环

- tools20 独立完整构建已真实 exit0/Job0，23 tests、0失败/错误/跳过、-Xlint:all -Werror；Maven25.4990862s、峰800382976 B、原源/编译源双MATCH。
- 回执：`J/logs/build-java-tools20.json`，SHA256 `bc68451ee76195095bbf2c8b3a2dc3424f59ff5914e5a99ed7f77dbf79151cec`。
- 可执行工具闭包：`J/build/java-tools20/ck3-control-build-tools/ck3-control-build-tools-0.1.0-SNAPSHOT.jar` 加同目录 `lib/*`；精确全部 SHA/bytes 在回执。不要猜 m2 路径或只 pin 主 jar。
- 本次共享修改限 `ControlBuild.java`、`ControlBuildTest.java`、`ControlCi.java`：生产统一 `--fail-at-end`，真实 CMD/default mvn 参数与非零37/Job0回归，ControlCi 最低完整测试数23。Root 表示这三件尚为 WIP，未据此声称已推送。
- 历史 MapCi05：真实外层 session70575 exit0；`J/logs/JAVA-MAP-CI-VERIFICATION05.json` 3750 B，SHA256 `d99e868202003f36ccad5d742b03cf0e9410d303bce1e9aa3ea4860351bdaa41`。2整叶strict/equality +6真实HTTP/0skip +3原Queue/feeder/reducer lineage，服务CLOSED、内外Job0。该资格仅 owner19+java07九模块快照；不外推当前17/改后canonical。

## 源变化与终态后已到的修复

原 Z MISMATCH 按回执保留。只读当前差异观察：`J/logs/JAVA10-SOURCE-DIFFERENCE-OBSERVATION01.json`，生成器 `BuildSourceDiff.java` 仅是本地只读诊断，不是新的生产构建入口。它列出20项当前 Z 相对 java10 快照差异，也包括终态后获准的修复；**不能把全部20项倒推为构建期间变化**。

差异涉及 admission batchtiming、军事实域 disembark/updaterwrites、holyobservation/siegecontribution 移出、warresultssource 资源，以及 runtime clockreader/adoption/performance/savedproof manifest。必须重新冻结新源并 fresh build，不能修改旧回执。

已收到的有限修复/采用，尚未再次 Java 验证：

1. `BATCHTIMING-SOURCE-FREEZE02.json`：FullBatchTiming.fields() → properties()，原9测试/golden保留。
2. optional 原坏 GBK44,218 B 已精确保全D；共享 capture 加 `-X utf8`/发布前严格UTF8，fresh02 实际 exit0/Job0；原字节44,230 B已导入 owned resource，SHA `2a040319fcbb9dfe5d8a7bd8e18818fe5bfa0a6c829fb4b9cf8432774e066a7b`。3main/16JUnit未放松。
3. `CLOCKREADER-SOURCE-FREEZE02.json`：显式 `xar.repo` 或 `XAR_REPO_ROOT` 找原 repo，避免 D snapshot 向上查找失败；预计20JUnit尚未执行。
4. Root 已授 closedadoption 独立256KiB JSONL行协议和真实临时事务入口收尾；owner 仍在收口。小 metadata/SDK/source 边界不可随之放宽。其 final freeze 由 runtime lead 汇总。
5. 军事域若干 actual golden 正在采用，不能把 capture PASS 当 Java PASS；下次完整图必须取新的有限冻结资源集合。

## 资源与恢复前检查

保留有限预算 `J/ROOT-JAVA-PHASE1-CAPACITY-RELEASE02.json`，review `2026-10-22T20:00:00Z`；到期不得自动续。磁盘同池 D4GiB/Z32MiB，m2<=2GiB/build<=768MiB/scratch<=512MiB/logs<=32MiB。java10实际 logical：build331811894、m2112333857、scratch31536552、logs5275550、tools30367390、artifacts989750 B。

RAM 附注 `J/ROOT-JAVA-PHASE1-RAM-ANNEX01.json` 已实际读回，1681 B、SHA256 `038ac93b997d7e83860314af85ddd59b76b76a22a89159bc6f0f6f95d6be6cd0`：联合6GiB；唯一 Maven 或服务树2GiB +最多4独立capture树各512MiB；新 dispatch 前可用RAM>=12GiB；源码冻结中capture只写D。SDK测量及原writer链独占，不能与这些并行。用户休假已停止新作业，附注不是继续执行许可。

## 下次用户恢复后必要入口与环境（现在不执行）

先消费各现有owner最终freeze/actual资源、重新读父图、机器ID、容量/lease及所有旧任务终态。保持默认 `mvn`、最低稳定>=3.10.0，不传绝对 Maven 路径，不改 PATH，不迁址。使用新的 attempt 名，例如 `java11`。

```bat
set "JAVA_HOME=C:\jdk-21"
set "TEMP=D:\codex-ck3-demos\2026-10-22-java-phase1\scratch"
set "TMP=D:\codex-ck3-demos\2026-10-22-java-phase1\scratch"
set "XAR_ORACLE_PYTHON=C:\Users\xenoa\AppData\Local\Programs\Python\Python313\python.exe"
set "XAR_REPO_ROOT=Z:\ck3_mod_rewrite"
C:\jdk-21\bin\java.exe -Xms32m -Xmx128m -XX:MaxMetaspaceSize=96m -XX:ReservedCodeCacheSize=32m -XX:MaxDirectMemorySize=32m -Xss512k -Djava.io.tmpdir=D:/codex-ck3-demos/2026-10-22-java-phase1/scratch -Djna.tmpdir=D:/codex-ck3-demos/2026-10-22-java-phase1/scratch -jar D:/codex-ck3-demos/2026-10-22-java-phase1/build/java-tools20/ck3-control-build-tools/ck3-control-build-tools-0.1.0-SNAPSHOT.jar --source-root Z:/ck3_mod_rewrite/java/ck3-control --work-root D:/codex-ck3-demos/2026-10-22-java-phase1 --capacity-release D:/codex-ck3-demos/2026-10-22-java-phase1/ROOT-JAVA-PHASE1-CAPACITY-RELEASE02.json --attempt java11 --owner-task /root/g2_m7 --java-home C:/jdk-21 --minimum-maven-version 3.10.0 --timeout-seconds 900
```

上述精确路径仅本机事实；跨机先实测 identity/工具及获准根。若 release 已到期须 Root 实测重新准入；不要直接运行到期旧卡。不要用 `-Duser.dir=Z:...` 破坏同卷快照/codegen；fixture 用显式 repo contract。

完整 canonical cold/warm/独立SDK continuation/27文件pytest CI组由 `/root/ci_portability` 收尾；本交接没有声称这些新组已PASS。15:30前SDK ticket是否仍有效及实际SDK测量由Root/sole owner复核，不从源码或旧结果继承。

未新增 retained-process API/新迁移组件。processcustody 草稿仍缺必要 shared retained-handle接缝，未注册，不混进当前17图；用户停止新迁移后不再扩展。

本轮没有 Game/RPC/ledger writer 操作，不能抵扣30年进度、G2 M7实机验收或1秒/日性能目标。
