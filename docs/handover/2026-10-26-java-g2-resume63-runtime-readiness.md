# resume63：现有进程与 Java 首场输入只读核对

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察窗口：`2026-10-26T15:31:19Z`–`15:39Z`。执行者 `/root/readiness63`；机器身份沿用本轮 Root 已实际核验结果。本文仅保存指定进程的 Win32 元数据与首场目录/小原件观察，不授予 Game、SERVICE、容量、发布、writer 或启动资格。

本岗没有启动、激活、移动或截图任何 Steam/游戏窗口，没有游戏动作、游戏内存读取、OCR、进程终止、Genesis 初始化或账本写入。唯一新增文件是本文，使用 Root 本轮分配的 Z 盘小文档额度，UTF-8 上限 16 KiB；没有新增 D/C 盘输出或平行 runner。命令均经 `cmd.exe` 与 base64；已有低层 Python 诊断以 `-I -B -X utf8` 执行，不新增 Python 生产实现。

## 三个 CK3 PID 实际已退出

Root 的 MCP status 列出 PID 不证明其正在运行。`2026-10-26T15:31:46.138295Z`，复用仓库 `tools/g2_saved_campaign/sdk_process_custody.py` 的 `WindowsProcessAPI`，以 `PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE` 打开实际 handle，逐项读取 GetProcessTimes、WaitForSingleObject(0)、GetExitCodeProcess、QueryFullProcessImageNameW 与 TokenUser。没有使用 WMI、缓存路径或进程名代替身份。

| PID | 实际出生 FILETIME 字符串 | held handle wait0 | exit code | 原生 parent PID |
| --- | --- | ---: | ---: | ---: |
| 127028 | `134361687131978541` | 0 | 259 | 169036 |
| 139512 | `134358608246743243` | 0 | 259 | 140764 |
| 188168 | `134362593694706725` | 0 | 259 | 191172 |

三者 TokenUser 均为 `S-1-5-21-2908730481-166481001-1318755029-1001`。**wait0=0 是这三个 generation 的内核退出事实；exit code 259 不覆盖它。** 首次调用较高层 `Windows.identity` 因 image 查询失败整体抛错，随后上述分项读回明确了失败范围。三者 QueryFullProcessImageNameW 均 WinError 31，实际 executable 完整路径仍 **UNKNOWN**，不能拿当前 installed ck3.exe 路径补齐。

parent PID 来自 `15:33:28.556489Z` 的 `NtQueryInformationProcess(ProcessBasicInformation)`。只读取内核返回元数据，没有解引用 PEB 或读取游戏内存。`15:34:59.120763Z` 后续 query 得到：

- 169036：OpenProcess WinError 87，无法取得 generation。
- 140764：birth `134358520985715966`，wait0=0，parent=168260；当前 168260 的 birth `134363058450102577` 晚于子进程，属于 PID 复用，历史链在此终止。
- 191172：birth `134362549441966160`，wait0=0，parent=139384；当前 139384 的 birth `134362983175080102` 晚于子进程，属于 PID 复用，历史链在此终止。

这些事实排除了“这三个指定 generation 是其他任务当前活跃游戏”的误判；本岗未做整机 live CK3 census，也没有据此授予新启动资格或操作未知进程。

## 当前 operator 仍仅绑定旧 Python 作业

operator PID 47384 实核 birth `134357171058866984`、wait0=258、session=1，image 为 `C:/Users/xenoa/AppData/Local/Programs/Python/Python313/python.exe`，TokenUser 同上。实际 parent 50532：birth `134357171058618462`、wait0=258，image 为 `Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe`。两者仍 live，不停止或接管。

对 operator 47384 的内核返回 command line（ProcessCommandLineInformation，仅解码当前诊断进程自己的返回 buffer）为：

```text
Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe -B -X utf8 Z:/g79/ck3_autonomous_player/operator_mcp_server.py --profile Z:/ck3_mod_rewrite_process_assets/g2-runtime-next-20261006/operator-profile-v74.json
```

实际 profile：3283 B，SHA-256 `789e15f23299c5b613d006782bf818029772500936dce6d5872049c57016e153`；target `xenoa-local-ck3`、endpoint `127.0.0.1:8766/mcp`。jobs 只有 `g2-robert-v74-h9537-native-session`，command 绑定 `Z:/g79/ck3_autonomous_player/agent.py`、旧 v74 state/profile 与旧 Native DLL/injector，**没有新 Java 作业路由**。不重放该旧 job。

profile 的 state_directory 为 `Z:/ck3_mod_rewrite_process_assets/g2-runtime-next-20261006/operator-r0048-state`。其中只有作业目录 `jobs/480e5d18-ac10-4ab1-a269-eb1e7c550f95`：handoff.json 1083 B、stdout.log 9907 B、stderr.log 0 B。handoff.json 留着历史 `state=running, exit_code=null, pid=39380`；它是历史创建记录。指定 39380 实际 query：birth `134357171772154456`、wait0=0、parent47384、同 SID，符合 Root 当前 MCP status 所报 exited。磁盘历史 running 不能反推当前 owner 或活跃作业。本核对覆盖该 operator 作业绑定，不代表全机所有 task bus 或调度器都已清点。

## Genesis 原件仍保持初始状态

STATE 为 `D:/ck3-state/ck3-java-g2-robert1066-resume61`。`15:36:21.677998Z` 对 initial-data 的 13 个 JSON 使用 held read handle 的 Native FileIdInfo/FileBasicInfo 与有界全文 SHA-256：11 个旧 DATA 加两个 Genesis。所有 64 位身份均保留十进制字符串，没有经过 JavaScript Number。

Genesis 两原件位于 `STATE/initial-data/ledger-genesis/`：

| 原件 | bytes | Native FileID 字符串 | creation FILETIME 字符串 |
| --- | ---: | --- | --- |
| ROOT-CONTINUITY-ANCHOR.json | 719 | `1970324853272922` | `134374926729141238` |
| ROOT-CONTINUITY-SNAPSHOT.json | 719 | `2533274806694228` | `134374926731709400` |

二者 volume serial 为 `6505083400996699863`，SHA 均 `c8a1451eceafcd6de8367fa0d5ef15bb35af8af13c23860d43da82ea48cc462a`，与实际 Genesis stdout 的原生身份逐项一致。内容仍是 `xar.java-continuity-pre-entry/v1`、sequence=0、window_id=0、status=`awaiting_initial_entry`；start/last-settled/target 日期及 latest_binding 均 null，修复与恢复计数为 0。此处 planned_window_id=1 是请求意图，不是已经发生的窗口或游戏 Origin。

账本目录实际有 5 项：`.runtime-storage-0ce655b4fb182d7dd32d7630c5c980c00a16672cfada85846cb7d40d4775ae91.lock`、anchor、snapshot、snapshot.lock 和 `ROOT-CONTINUITY-WINDOW-EVENTS`。两个 lock 为 0 B，events 目录空。本岗未获取 writer 锁或修改它们。**不得再次 create Genesis。** App 后续仍消费当前 snapshot 路径和实际 anchor ExactRef。

原始证明来源：

- `STATE/bootstrap-execution/quote01/readiness/genesis-create01/stdout.log`，2354 B，含原生 anchor/snapshot/lock 身份。
- `STATE/bootstrap-execution/quote01/metadata/issuer12-genesiscreate01/ACTUAL-GENESIS-CREATE01-CLOSE01.json`，4620 B，SHA `351ab8143aeefcf7f2e59207023555dbcc61dfb07f6dec05bf784601eabcbcda`。

## 旧 11 个 DATA 原件可定位，不循环重生成

以下均相对 `STATE/initial-data/`，合计 5846 B；同 volume serial `6505083400996699863`。这是原件身份核对，不是重新授予过期 payload、binding、census 或 source review 资格。Sway 旧 CREATE 不重放；任何替代发布仍由真实 typed producer 和独立 issuer 完成。

| 相对路径 | bytes | FileID | SHA-256 |
| --- | ---: | --- | --- |
| capability/capability-configuration.json | 339 | `281474992984970` | `b9d68ae2c197be2d1cd4772f7fe76872de79779f3cbdb08a640b5f30e5acba7d` |
| capability/capability-session-presentation.json | 398 | `562949969695620` | `4a2bd2bb8e1b46a90b4532fcbe6ff4103744f96481800ea9dd4c1010f148d883` |
| event/trusted-event-source-context.json | 342 | `281474992985009` | `7b33a5a050d8a06e9f2dfe7ae9a71cbe1a38b0ae5c59826ddc71f5edadd1dac9` |
| family/child-matrilineal-domain.json | 94 | `281474992985178` | `39ec5f18eebace44ecc9003a3d836820bf395dd2ad406735a3dc7958978a2913` |
| family/default-marriage-domain.json | 82 | `281474992985179` | `bed0b40cda5155978f21720c3dad6942d42e6564a60e41c3763e83eba2afd3a0` |
| family/family-domain.json | 81 | `562949969695826` | `f552d8487d91a9a220366e883e37c230076a5dd898fe4aea38bfb327e2f02cca` |
| planner/coa-read-limits/coa-read-limits.json | 119 | `281474992985135` | `23ca615be307a657f648db7779ec02f8416aaee684ffb66a3c35270c136c160f` |
| planner/core/advance-timings.json | 130 | `281474992985092` | `a1288705da5ec8b181a1ad255636e647523702ac5cd86c626cbf6aa267b5fae4` |
| planner/core/campaign-deadline.json | 3515 | `562949969695744` | `d67eec3f8200d0bfcfdf046df19fc43050102896b2f9af2b81e2744fe404be6b` |
| planner/core/life-settings.json | 135 | `281474992985091` | `26fc2bca72f96ab75fcb42026eaefd49bb5110ecab3efa3ddae718af6e9085d2` |
| sway/SWAY_CONFIGURATION.json | 611 | `281474992985051` | `14cab7af27405274e06a2817f169484db3aefb6a599a3469bc9eb34f924594cf` |

22 角色表对应已存在的 10 个必需角色为 01/02/03、08/09/10、16/17/18/19；CoA 119 B 仅角色20辅助来源，不把它算第11个必需角色。角色22仍沿既有历史 manifest 的明确选择，不重新全量生成或把历史 machine unknown 追认为本机捕获。

## runtime 根与仍缺的真实输入

`reference_main/firstlive_parameters85/PARAMETER-SELECTION85.json` 只作参数意图，已选择 artifactRoot 为 `STATE/root-robert1066/state/immutable-artifacts`；当前该路径不存在。`STATE/root-robert1066` 的 state/saves/queue/driver 四目录都空；driver-state.json 不存在。`STATE/native-runtime` 为空，profile/userdir 不存在。`STATE/initial-data/application`、native-plan、runtime-definitions、startup、finite、runtime-invocation 均为空。

实际 Definitions 尚未产，现存 Request 与已读参数选择中没有 incidentBase/scanBase 的实际配置值；不能猜路径再把猜测当作已覆盖库存。真实 `RootRuntimeDefinitionModel.IncidentInputs` 要求二者绝对且互不包含。先落实这两个真实输入，再连同 artifactRoot、ledger 做同窗口完整 declared-root census。当前只读目录观察不是生产 `RootRuntimeStorageGuard` census，旧空 ledger census/lease 不可复用；新窗口没有同窗口前头时 generation1/null，旧 claim 算 other，不冒 gen2。

公共新 Root 入口沿现有源码：

1. `RootRuntimeLaunchCommand.prepare(actualManifest, actualInvocation)` → `JavaRuntimePackage.readAccepted` → `JavaRuntimeLaunch.prepareRoot`。其 main 接 package-manifest exact3、Root-invocation exact3、stdout、stderr、canonical whole-JVM memory bytes，共9参数；输出状态明确 `COMMAND_PREPARED_NO_JOB_ADMISSION`，不能据此启动或认定 Game。
2. `RootFiniteFirstLiveMain` 是 Quarkus named main `finite-first-live`，SERVICE 构建选择 `-Dquarkus.package.main-class=finite-first-live`。运行接 actual request path/bytes/SHA 三参数，沿 RootStartupInputsProducer 和现有 host/work 实体生命周期。
3. 本轮 SRC 的 RootProfileBootstrapCommand 已实际出现显式 `FILE_REPLY CHANNEL_PATH BYTES SHA` 后缀与 `ISSUER_FILE_REPLY` 分支；这是源码存在性检查，未授编译、测试、issuer、CREATE 信用。RootInvocation/v5 候选仍待原 producer→Shared→LS/reader→测试全部闭环，不能直接消费旧不兼容 CommandSpec。

启动前未完成项仍包括：真实完整 Tools VERIFY/LS 与对应受影响回归、原 SDK30 组、具名 genuine SERVICE_FAST_JAR/JavaHome/source closure；实际 PROFILE production/manifest/ENV、policy/run-profile、NativePlan；原 MCP capture、两阶段 admission 与最终 Definitions、剩余 domain settings/native originals；Application/Startup/finite/package/invocation；新的完整容量与 runtime authority、实际 Native EXE 登记读回。旧 ordinary Jar、HTTP/ACK/源码采用都不能补齐这些实体。

本轮没有刷新 Steam 状态。启动前按既有 `tools/steam_offline_state_probe.py --receipt <new-path>` 后台新鲜读回，仅 `status=offline` 且 `offline_mode=true` 的同机实际来源回执用于离线准入；unavailable 不截图、不抢焦点、不自动联网。历史离线回执只证明其观察时刻。

## 存储与复核边界

已读通用策略及版本化参数。机器 root map 实际原件：`Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/machine-storage-profile-final.json`，1900 B、SHA `72c76ba7b1d9281403c55a5b6ec2079d4137fbe88497e1f18a0b3493fcc44d2e`。其 machine_id 与本轮一致，background=`D:/codex-ck3-background`、state/temp=`D:/ck3-state`、main=`Z:/ck3_mod_rewrite`；旧 available_bytes 是历史事实，不作新容量准入。没有 bulk C 盘回退或全局 TEMP/PATH 改动。

本记录优先在下一次真实启动准备时刷新，最迟 `2026-11-02T15:36:21Z` 复核用途；不是对原 hold 自动续期，也不是清理授权。M0–M7 新增实机完成数、游戏日、SAVE/RESTORE 与启动均为0。
