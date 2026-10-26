# resume63：Native helper 回归、类型范围与 R34 独审

> 后继来源纠偏：下文原 103 项、201 个类型诊断和四叶 pin 均保留为旧 Root cohort 历史，不能整文件合入较新的远端。最终可交付的是本文末尾“e735 前向合并与最终维护范围”的两 helper after-image；fresh 四模块实际 127/127 PASS。configured 两叶与 e735 完全相同，无本轮交付差异。

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察于 2026-10-26 UTC；最终软件执行完成于 `14:55:04.229704Z`。机器身份实际执行 `py -I -B -X utf8 tools/ck3_live_run_id.py machine` 核对。承接 [resume62 交接](2026-10-26-java-g2-resume62-rea-runtime-handoff.md) 的 Native 软件与 R34 源审工作。

本包最终原四模块 **103/103 PASS**，未跳过。严格 mypy 的明确提取范围及两个完整 configured 模块通过；完整 helper/test 两叶仍有 **201 个诊断**。R34 两叶候选完成全稿独审及精确重放，适合进入后继 Host 源码采用和局部编测；它尚未采用、编译、运行或获得登记资格。本包没有启动 CK3、执行 UAC、重放 REGISTER21，或修改冻结 Source15/S26/native 构建缓存。

## 修复与最终来源

真实第三轮回归中，failed link 在 `allocated()` 枚举输出之后删除了部分 `direct.exe`，随后 `Path.stat()` 抛出 WinError 2，使旧软件回归报错。共享 [build_native_configured_successor.py](../../tools/build_native_configured_successor.py) 现在仅忽略该已消失文件的 `FileNotFoundError`；权限和其他 I/O 错误继续抛出。补了两个确定性回归，分别验证其余文件仍被计入，以及非缺失错误仍失败。

[helper 测试](../../tools/test_register_project_exe_exclusions.py) 收紧了新增 11 方法、控制 COM provider、结果读取与 fixture 复用的类型边界。原 fixture 用组合复用，未复制或继承运行另一批旧测试；可空读回先窄化，未知 JSON 值先校验。没有新增 `Any`、`cast` 或 `type: ignore`。生产 helper 仅将现有 `add_path()` 返回字典标为 `dict[str, object]`，未更改登记结果判定。

| 修改文件 | 最终字节 | SHA-256 |
| --- | ---: | --- |
| `tools/register_project_exe_exclusions.py` | 32978 | `46df4c1cec6ff266553b42724cd02790c13b198ee69e2cb781be03b7460dc842` |
| `tools/test_register_project_exe_exclusions.py` | 39842 | `126decfb07f9fab5b76ff5c061a9515908ca136677355342645ba05d0578966c` |
| `tools/build_native_configured_successor.py` | 58640 | `abd3ae5b48a5ca05f1e7fa82d50a2e97d783a38268063af47aa7592cff0c7d3e` |
| `tools/test_build_native_configured_successor.py` | 12258 | `b45b5062db26a5f76d3d755efeaeaea84ceb430a217c402d0070d2049b87c5ac` |

完整六叶来源还包括未修改的 broker-client 与 MSVC-evidence 原测试，见 [NATIVE63-REVIEW01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/NATIVE63-REVIEW01.json>)（5045 B，SHA `75aa642a8bcc07ed5949cdd6074cf96481be9c0350678dda6830ef95c0c3af66`）。`git diff --check` 对四个修改文件实际通过。Git 集成交由 Root；本岗未提交或推送。

## 完整软件回归与真实失败

实际 cwd 为 `Z:/ck3_mod_rewrite/tools`，原四模块命令为：

```text
Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe -B -X utf8 -m unittest -v test_register_project_exe_exclusions test_project_exe_exclusion_broker_client test_build_native_configured_successor test_run_native_msvc_evidence_dir
```

后继软件环境显式设 `CI=true`、`PYTHONDONTWRITEBYTECODE=1`，`TMP`/`TEMP` 为 `D:/ck3-state/ck3-java-g2-resume63-native-helper01/private`。四模块中的原配置回归实际编译三个微型 C++ fixture，验证真实直接链接失败、惰性 archive 链接及运行；这不是生产 Native 全图构建，也不授予实机资格。

| 轮次 | 实际结果 | 原因与保留边界 |
| --- | --- | --- |
| 初始 controller 环境 | exit 1；未启动 child | pywin32 `CreateJobObject` 拒绝空名称；改用明确的临时 Job 名称，未改变测试源码 |
| UNITTEST01 | 101 项，100 PASS / 1 FAIL | 未设 CI；原 MSVC fixture 读取本机 opt-in，调用实际自动登记 hook，返回 `settings_failed`。临时 helper 回执随原 fixture 清理，不能从最终软件计数追认该轮逐调用设置审计 |
| UNITTEST02 | 101/101 PASS | 显式 CI 软件环境；不是实际管理员登记通过 |
| UNITTEST03 | 101 项，100 PASS / 1 ERROR | 原 `allocated()` 遇已被 linker 删除的 `direct.exe`；真实堆栈保留，随后修共享生产入口 |
| UNITTEST04 | **103/103 PASS**；exit 0 | 新修复后最终完整四模块；内层 6.523 秒，受管观察 6.839 秒，无跳过 |

原日志和各轮回执均保存在 [软件状态目录](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/>)。最后回执为 [UNITTEST04-ACTUAL01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/UNITTEST04-ACTUAL01.json>)，stderr 17848 B，SHA `f4d3767cdf94268a0b11e27355c0d2388e9b83a52e6b1e22015af236db9fd114`。

每轮软件进程属于 2 GiB hard Job。最后 cohort 峰值 139419648 B；两个 main 自然退出后仍有一个所拥有的 MSVC 辅助进程，执行仅限该 Job 的清理后读回 `ActiveProcesses=0`。辅助进程清理与 unittest 自然 exit 0 分别记录，不能称所有后代自然退出。首轮 controller 在发现辅助成员后关闭已设 KILL_ON_JOB_CLOSE 的 Job，但没有取得其自然 Job0 读回；该失败不被后继覆盖。详见 [SOFTWARE-CLOSE04.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/SOFTWARE-CLOSE04.json>)。

## 实际静态类型范围

复用已有 `D:/ck3-state/ck3-java-g2-r4-dependency-setup53/test-venv54/Scripts/python.exe` 的 mypy 1.15，未安装依赖，缓存全部位于上述 D 根。

- 两个完整真实模块：`build_native_configured_successor.py` 及其完整测试。
- 精确 AST 提取：`ExclusionSettings`、`DirectSettingsReadback`、整个 `DefenderWmi`；`FakeWmi`、`RegistrationTest` 的三个已收紧 fixture 方法，以及新增 11 测试、控制 provider 和 JSON 窄化函数。方法体直接从实际源码提取，来源行号和 SHA 有映射。
- 旧 manifest 收集与 `register_manifest` 动态调度只提供 type-only 边界声明，不声称静态检查了其实现。六个 pywin32 外部 import 按模块窄列 `ignore_missing_imports`，它们的 COM 实现和缺失的第三方 stubs 不在静态通过范围；原完整回归仍执行真实 Python producer/consumer 与控制 COM 边界。

该明确范围 `--strict --follow-imports=normal --no-incremental` 实际 **PASS，4 source files，2.578 秒**，见 [MYPYSCOPED01-ACTUAL01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/MYPYSCOPED01-ACTUAL01.json>)。精确命令、[范围映射](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/TYPECHECK-SCOPE01.json>)和[本地提取 recipe](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/TYPECHECK-RECIPE01.json>)均可读。recipe 仅为本地验证材料，重现时需显式选择新的获准输出根；没有新增 Python CI module 或 runner。

完整原 helper/test 两叶也实际执行了 `--strict --follow-imports=skip --no-incremental`，最终 **exit 1 / 201 个诊断 / 2.278 秒**；先前 270、207 个诊断保留。旧未类型化字典、旧测试别名及外部 stub 缺口没有被压掉。不能将提取范围通过外推为完整原模块全绿。Root 负责将原四整模块及已有 configured 两完整模块类型检查接入持久 CI；不在 CI 新挂一个会掩盖旧债的“全叶通过”声明。

## R34 全稿独审与下一采用窗口

完整 [R34 候选包](</D:/ck3-state/ck3-java-g2-r5-native61/controls/uac-current23/UAC-CURRENT23-JAVA-RAMOPS01.json>) 119933 B，SHA `34bde6e8ea25923c04c90c67b3641639ff08f85e9e1e1a8b4ac667de5bd5bc02`。本岗读完整重建后的 main/test，核两叶前像以及 9+1 操作的每次唯一匹配；内存重放后 main 124891 B / `62344ed34f819a3730b68a47002461beb08bbfe3ac3e1739dca098caff33086f`，test 24351 B / `8b91d1198555a447bff05fb8ce06a724efdb5a773bd8e2e0bd8b02278cc2e4ea`，全部符合原包预期。

五个实际消费者 `NativeBridgeBuild`、`NativeBridgeDefender`、`NativeRegistrationRuntimeInventory`、`SharedOwnedCommand`、`WindowsJobProcess` 的当前源码与原 S26 对应源码逐字节相同，原保存 pin 全部 MATCH。新父进程仅做原 Shared standing 的元数据校验；真正的 S26 保留自己的独立 classpath 与 loaded-runtime 检查。后验先读取原 26 字段 v2 Java terminal，再走原 `readAccepted(REGISTER)`、manifest/helper 回执和新增 full SID / helper PID / 三数组检查。原两 target API 和旧资格 reader 保持原证明范围；新路径交给下游的是原格式 accepted REGISTER Actual。

一次性 Java current-plan 先核实际 elevated TokenUser 与同一 owner，再写 child intent、启动原 Shared REGISTER。它与旧 API 共用唯一 `ShellExecuteEx` 实现；未知结果不重放，不外部 Add 后导入回执，不安装 broker，不改 D 盘 ACL。

独审结论及精确来源见 [R34-REVIEW01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/R34-REVIEW01.json>)（3516 B，SHA `4b026c7c50699a6ea8a14aa5b90f4033d84302848db79e6cd0f98700246b5382`）。原完整操作可交 Host 的**后继 Tools cut**，本轮 Maven-argument 独立验收不夹带它。采用前再核前像和新鲜预算，随后实际编译并跑 `NativeProjectExeRegistrationTest` 的原 81-case 回归与新增三个用例。

实际登记仍需要：最终 helper 的 fresh full runtime inventory、新完成 publisher、原 S26 独立运行闭包、accepted ENV22/BUILD24、具体 current-plan、同窗口 whole-slot 联合资源/容量和实际 owner SID。最终 helper 已变为本页 32978 B 的新 pin，旧 helper23 inventory 不得复用。没有从 UAC ACK、软件测试或源审授予设置写入、NativePlan 或 Game 完成。

## 容量与保留

准入为 [CAPACITY63-TASK-START01.json](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity/CAPACITY63-TASK-START01.json>)，本岗 D complete cap 40 MiB、Z 文档 32 KiB；没有新 venv 或 C 盘大输出。源代码、缓存和证据按统一存储策略保留：raw 30 日，mypy cache 7 日，小型 record 180 日复核；当前必要基线仍最迟 2026-11-02T14:11:19Z 复核，不自动续期。闭场实际占用与完整输出清单见本状态根的 `STORAGE-CLOSE01.json`；首轮缺失的自然 Job0 不会改记为空。

## e735 前向合并与最终维护范围

`machine_id: xenoamess-full-tower-eb9d2c1186`；后继实际回归完成于 `2026-10-26T15:16:21.601457Z`，严格提取范围检查完成于 `15:18:25.590100Z`。Delivery 独审发现旧 Root 与远端有显著漂移，故本岗没有把上文旧四叶覆盖远端。固定基线为 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c`，仅在已有 D 状态根建立 14 个必要来源叶的有限组，逐叶按该提交的 Git blob 和 SHA-256 核对，未复制完整仓库、SDK 或新建工作树。

前向合并保留远端 helper 的 `Mapping/Sequence/Never/NotRequired/current_machine_id`、收紧的 receipt 类型、DLL-only 的 not-applicable 分支及原有测试扩展。只接入原 helper23 的直接 WMI 三数组读回、实际 TokenUser SID/PID、每次 Add 后读回和 11 个相应回归，以及这些变更的明确类型；没有增加 Python 业务能力或新 runner。普通 token 的隐藏空数组不能作为设置验证。两叶差异为 helper +117/-7、test +334/-7，原远端 class/function 名称全部保留。

| 最终交付叶 | 字节 | SHA-256 |
| --- | ---: | --- |
| `tools/register_project_exe_exclusions.py` | 35807 | `2b99d22175801b7fd8e61cd8a77ba92e5b5fdd1d12feef779a3e08e2a8183c24` |
| `tools/test_register_project_exe_exclusions.py` | 43745 | `80adc236eb98d0c77f7202f98938882187c60d03f7164650dce93ccbee024174` |

两 after-image 位于 [fresh-source/tools](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/fresh-source/tools/>)。完整前后像及 12 个不变依赖的 pin 见 [SOURCE-AFTER02.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/fresh-source/SOURCE-AFTER02.json>)，逐叶窄差异见同目录父级的 [FORWARD-REVIEW01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/fresh-source/FORWARD-REVIEW01.json>)。原 root 用户树未被 fresh after-image 覆盖，本岗没有提交或推送。

远端 configured producer 已有相同 `FileNotFoundError` 修复，并已有“枚举后实际删除”“权限/其他 I/O 错误继续抛出”的两项确定性回归。因此最终未重复追加两测试，configured producer **110409 B** / `54e32751a76fc260d28a3d23c8b76c8aa49f631c828f276b775bbb2395f37628`，test **70433 B** / `1df222ed9b1d1d683460b05ce70f75f2ae09f79c56480645416f0b02e40a4e19`，均与 e735 逐字节相同。上文旧本地 58K/12K 文件不得用于覆盖这两远端叶。

fresh 来源有最小私有 Git metadata 和只读 objects alternate，`git rev-parse HEAD` 实际读回上述固定 e735；没有把根仓实际旧 HEAD 冒充来源提交。首轮把 Git 环境变量传入子进程，干扰了测试自建 Git repo，并把临时目录误置于 fresh ROOT 内，且选用的旧环境缺 mypy，导致 **129 项中 1 FAIL / 15 ERROR**。这些失败及第一份私有 metadata 保留。修复执行环境后使用新的私有 metadata、独立测试 Git repo，`TMP/TEMP` 移到 fresh ROOT 外的 `fresh-private02`，并复用已装 mypy 的 D 盘环境。最终测试中没有放宽 source/output 边界守卫。

实际 cwd 为 `D:/ck3-state/ck3-java-g2-resume63-native-helper01/fresh-source/tools`，`CI=true`，Python 导入只指向此精确来源组。完整命令为：

```text
D:/ck3-state/ck3-java-g2-r4-dependency-setup53/test-venv54/Scripts/python.exe -B -X utf8 -m unittest -v test_register_project_exe_exclusions test_project_exe_exclusion_broker_client test_build_native_configured_successor test_run_native_msvc_evidence_dir
```

[FRESH-UNITTEST02-ACTUAL01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-UNITTEST02-ACTUAL01.json>) 记录 **127/127 PASS、零跳过、exit 0**；内层 35.152 秒，受管观察 35.647 秒。实际原配置回归包含微型 C++ fixture，未启动游戏或生产 Native 构建。该 cohort Job 上限 2 GiB、实测峰值 **306032640 B**；main 自然退出后有两个所拥有的辅助成员，单独清理该 Job 后实际 `ActiveProcesses=0`。见 [FRESH-SOFTWARE-CLOSE02.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-SOFTWARE-CLOSE02.json>)；辅助清理不被记作 main 自然退出。

完整 fresh configured 两模块按既有 CI 参数执行 `mypy --strict --follow-imports=skip --no-incremental --cache-dir nul`，**PASS / 2 source files / 1.680 秒**。完整 argv 见 [FRESH-MYPY-CONFIG02-ACTUAL01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-MYPY-CONFIG02-ACTUAL01.json>)。两 helper 的实际新增类型范围按上述 AST 方法从最终 fresh 文件重提取，**PASS / 2 精确提取 source files / 1.475 秒**，见 [FRESH-MYPY-SCOPE02-ACTUAL01.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-MYPY-SCOPE02-ACTUAL01.json>)、[42 节点映射](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-TYPECHECK-SCOPE02.json>)与[精确本地 recipe](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-TYPECHECK-RECIPE02.json>)。旧 manifest/dispatcher 的 type-only 声明仍不构成其实现的严格检查；外部 COM stubs 仍是明确排除范围。上文 201 个诊断仅属于旧 Root 两叶，本轮未重跑 fresh helper 两完整叶，不能把旧数目移植给新来源，也不能宣称全叶严格通过。

Root 最终把 CI 改动收敛到已有独立 registration step：保留原 registration，追加 broker-client 和 MSVC-evidence 两模块，并设置 `CI=true`。configured 原 step 及它原有的三个完整 SDK 消费者、严格检查命令保持原样；本岗只读检查了这些依赖入口后停止扩大范围，没有物化或下载 SDK。三个原 SDK 消费者在本包**未执行**，127 项不冒充该完整 step 通过；官方 CI 继续执行原命令。此维护未更改 SDK、cold/warm、持久化或请求合同。

R34 源审结论不变，仍只交给 Host 的后继独立 Tools cut。真正采用后必须据最终 helper **35807 B** 的 fresh pin 重建 full runtime inventory；上文旧 32978 B 及 helper23 inventory 均不能授新登记资格。此软件 cohort 的 UAC/settings/Game 调用均为 0；首轮旧 UNITTEST01 的不可恢复逐调用审计边界仍按上文保留。

最终机器可读交付见 [FRESH-READY03.json](</D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-READY03.json>)；含 old/fresh cohort 的明确区分、来源、实际结果与静态范围。最终容量读回见同根 `STORAGE-CLOSE02.json`，仍按原 40 MiB complete cap 和期限保留；没有释放其他 Native 预算或创建新 venv。
