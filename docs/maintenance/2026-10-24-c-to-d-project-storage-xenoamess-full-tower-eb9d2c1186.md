# 项目工作目录从 C 盘迁至 D 盘（2026-10-24）

`machine_id: xenoamess-full-tower-eb9d2c1186`。整体状态：**IN_PROGRESS**。
本进度稿建立于 `2026-10-24T15:44:42Z`，本次按实际回执更新至 `2026-10-24T15:48:35Z`。
42 个状态目录的迁移、联接切换及旧 C 载荷清理已完成；背景目录复制、worktree 修复、Defender 新路径登记与容量闭账仍在进行。
本页不将状态文件迁移、MCP 静态查询或 Java 测试通过写成全部迁移或 CK3 续接验收完成。

## 范围与选址原因

用户授权迁移本项目的两类大目录，并要求后续大体量工作输出避开系统盘。系统 `LOCALAPPDATA`、`TEMP`、账户配置、
已安装依赖及其他项目不随本次项目根迁移。

| 用途 | 原位置 | 目标位置 | 当前状态 |
| --- | --- | --- | --- |
| 背景源码工作树、构建、冻结来源及证据 | `C:/codex-ck3-background` | `D:/codex-ck3-background` | 复制中；最终清单、校验和切换回执待补 |
| 原 `XarAutoplayer*` 隔离状态和场次 | `C:/Users/xenoa/AppData/Local/<原目录名>` | `D:/ck3-state/<原目录名>` | 42 个目录全部 `VERIFIED`，旧入口均为准确指向 D 的联接，退役 C 载荷均已不存在 |

`state-migration-final.json` 于 `2026-10-24T15:45:53.226180Z` 实际记录
`ALL_42_VERIFIED_CUTOVER_AND_SOURCE_REMOVED`；每根均有 `junction=true`、`resolves_exact=true`、
`retired_source_absent=true` 和 `verify_status=VERIFIED`。精确 42 对旧/新路径保存在该回执，不把前缀匹配当作额外删除范围。
同一时点 C 可用 **76,649,082,880 B（71.39 GiB）**，D 可用 **726,716,248,064 B（676.81 GiB）**。
这是阶段容量快照，背景复制仍在写入，空闲差额不排他归因本次迁移。
背景目录约 287 万文件是复制进行时的规模反馈，最终文件数和字节数待完成清单确认。

历史背景构建转到 C 盘的明确原因是当时 Z 盘容量不足，见 [2026-W41 记录](../autonomous-agent-progress/weekly/2026-W41.md)
和[当时的 sparse lane 说明](../ck3-native-ai/combat-phase-warmonger-predicate-12003.md)。
自动游玩状态原位置来自 `%LOCALAPPDATA%/XarAutoplayer` 的用户隔离默认值，入口已有显式 state 路径配置。
本机 D 盘为机械盘，容量迁移不构成性能改善结论。

## 执行与兼容边界

本轮按[通用存储策略 1.0.0](../storage-retention-policy.md)检查目标卷、复制峰值、并发预留、配额和期限。
实际准入见 `admission.json`：`2026-10-24T15:07:24.805080Z`、owner `c-to-d-project-migration-20261024`，
状态 `ADMITTED_USER_AUTHORIZED_RELOCATION`；D 当时可用 **844,950,630,400 B**，迁移峰值预留 **256 GiB**，
系统增长预留 **64 GiB**，安全量 **20 GiB**。项目用量保守计入当时 D 全部占用，采用此次用户授权迁移专用的七日配额例外，
截止复核时间 `2026-10-31T15:07:24.805080Z`。准入明确 `new_game_or_build_admission=false`，
删除范围只包括已验证迁移的原副本。最终容量闭账仍待完成；移动到 D 盘不刷新原资产寿命，也不扩大永久保留例外。

复制、文件内容验证、目录联接切换、旧副本删除及最终容量读回分别记录。跨卷后的卷身份和 FileID 是新副本事实，
原 SHA、来源、历史路径、时间、GREEN/RED/UNKNOWN 及失败回执保留；旧副本删除后另记原件可用性和精确替代位置。
清理只覆盖本次计划内、已完成切换的旧副本，不递归跟随 C 盘联接进入新的 D 盘载荷。

后续任务显式使用 `D:/codex-ck3-background` 与 `D:/ck3-state/<工作包或原目录名>`。
已有 MCP 注册的 `--state-dir`、`--userdir` 和解释器绝对路径优先于环境变量默认值；现有注册、venv、冻结 profile、
checkpoint 和账本不能因复制及旧入口联接仍可读而自动取得新路径资格。新的直接 D 路径合同继续通过现行准备、rebind 和资格入口产生，
不对旧冻结 JSON 作批量路径替换。本轮现有 MCP 的配置更新与静态验证范围如下；未重新准备游戏 profile，也没有执行 CK3 恢复或动作。

linked Git worktree 需要复核 common-dir、双向登记、exact HEAD 和 dirty/untracked 内容；继续开发的新物理路径按
[worktree 迁移流程](../branch-management.md)修复并读回。旧构建 cache 和启动 argv 的绝对路径不作无条件可移植承诺。
新 EXE 完整路径的 Defender 登记与实际设置读回另按[现行专题](../ck3-native-ai/project-exe-defender-exclusions.md)处理，旧 C 盘设置不外推到 D 盘。

## 后续写入配置与代码范围

`registrations-and-environment.json` 于 `2026-10-24T15:12:29.319018Z` 保存以下用户环境实际值，旧值均为未设置：

| 配置 | 实际值 |
| --- | --- |
| `XAR_AUTOPLAYER_STATE_DIR` | `D:/ck3-state/XarAutoplayer` |
| `XAR_PROJECT_STORAGE_ROOT` | `D:/codex-ck3-background` |
| `XAR_CK3_BACKGROUND_ROOT` | `D:/codex-ck3-background` |
| `XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK` | `true` |
| `XAR_PROJECT_TEMP_ROOT` | `D:/ck3-state/tmp` |

环境变更广播返回 **1**；新启动进程读取新用户设置，已经运行的 Codex 进程环境不会因此改变。
`2026-10-24T15:48:35Z` 在 `Z:/cmig24` 通过 `git config --local --show-origin --get` 逐项实际读回：
共享 `Z:/ck3_mod_rewrite/.git/config` 中 `xar.projectForbidSystemVolumeBulk=true`、
`xar.projectStorageRoot=D:/codex-ck3-background`。这两项 Git-local 设置使同一 common-dir 的现有工作树可读取本机 opt-in。

Java 守卫依次读取 JVM 属性、进程环境和 Git-local opt-in，检查输出最近存在祖先解析后的实体卷；拒绝系统卷实体输出，
不迁移输入、安装路径或小型元数据，也不宣称已经拦截全部旧生产工具。

本次补丁在 `ControlBuild.buildExclusive` 接入同一守卫，覆盖普通 verify 和 capture 构建；
`SdkSourceAssembly.assemble`、`assembleViews` 与 `assembleReference` 在批量写入前调用该守卫。
未接入的旧工具仍须逐次核对实际输出根和峰值。
现行说明同步到 [AGENTS](../../AGENTS.md)、[自动游玩 README](../../ck3_autonomous_player/README.md)、
[账户 MCP 安装说明](../ck3-portable-codex-mcp-setup.md)和[工作树迁移说明](../branch-management.md)，不替换历史报告中的旧路径。

## 已完成的 MCP 配置与静态验证

同一份 `registrations-and-environment.json` 保存 `C:/Users/xenoa/.codex/config.toml` 的旧副本和前后 SHA，
本轮只更新 `ck3-causality` 的 state 路径及 environment manifest 路径到 `D:/ck3-state/XarAutoplayer-1.20.0.3-migration`，
并移除已退役的 nonwar 开关；其余 MCP server 保持。配置 SHA 从
`0cc5fe5f2b54e7273f7f8e84fa6e528ecb904be4113aba26b71677f2f30d0370` 变为
`c29f0b6a453f9fdfbd476cc900d7c43bb19a630f0df47d60a1cd935e206b6801`。

`mcp-destination-final-verification.json` 于 `2026-10-24T15:31:52.591850Z` 实际完成 MCP initialize、list-tools，
枚举 **122** 个工具，并调用历史静态事件知识 `health.1015`，响应可用且 `knowledge_is_error=false`，
结果 `MCP_TRANSPORT_AND_OFFLINE_KNOWLEDGE_VERIFIED`。122 是该次源码的观察结果，不是 ABI 常量。
查询返回的是既有 **1.20.0.3** 知识数据，不证明当前 CK3 安装版本、native 可用、profile 合格或游戏业务完成。
该次验证没有启动/操作 Game，也没有重新 prepare profile。

## 已完成的必要 Java 验证

验证机器为本页 `machine_id`，观察时间 `2026-10-24T15:26:42Z`。
独立 sparse worktree `Z:/cmig24` 固定在 `85905d4ced48e59f826aa6bb92245af7dd1ea5d9`，移植本轮文档和守卫，
未混入主工作树的其他既有 dirty 内容。默认 `mvn` 实读 **3.10.0**，Maven home `C:/apache-maven`；JDK **21.0.10**，`C:/jdk-21`。
这些路径是本次观察事实，后续执行继续使用机器默认 `mvn`。

使用既有 `D:/codex-ck3-demos/2026-10-22-java-phase1/m2`，build、`java.io.tmpdir` 和 `jna.tmpdir` 均位于
`D:/ck3-state/storage-guard-verification-publication`。完整编译 build-tools 的 **76 个生产源码、94 个测试源码**，
启用 `-Xlint:all -Werror`；实际只执行 `ControlBuildTest` 22、`ProjectStoragePolicyTest` 10、
`SdkReferenceAssemblyTest` 4、`SdkSourceAssemblyTest` 25，共 **61 项，失败 0、错误 0、跳过 0**。
Maven exit **0**，日志报告 `Total time` **33.708 秒**；其余测试已编译但未执行，没有启动 CK3 或 Steam。

外置 [VERIFICATION.actual.json](D:/ck3-state/storage-guard-verification-publication/VERIFICATION.actual.json) 记录范围和机器身份；
同目录 `default-maven.log` 为版本读回，`maven-test.log` 的 SHA-256 为
`21174aca43bfce79f21f3d49eecb342c942f1a5d4a3e06909af1e41d37cc4063`。
本次测试结果只证明选定存储守卫和 Java 构建入口兼容范围，不抵扣目录迁移或游戏状态接续的实际验收。

## 已读取的迁移阶段回执

以下原件均绑定本页 `machine_id`，位于
`Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/`。
本次只读取和哈希这些小回执，没有重新运行迁移或 Java 测试。

| 回执 | 大小（B） | SHA-256 |
| --- | ---: | --- |
| [state-migration-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/state-migration-final.json) | 13,330 | `4f436cda1a7bc88d80a29fa717ada5522fcaf383731b4f994d125e02d33ae55e` |
| [registrations-and-environment.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/registrations-and-environment.json) | 1,842 | `24de6f10d90ce8b8841f0729d08869c82aa5456bcdf6b70e5ff0d2e6d42482d5` |
| [mcp-destination-final-verification.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/mcp-destination-final-verification.json) | 115,816 | `5de7b270ca44a6fa924d0d735b6c21be8ad70a5550cde72045d7f30258fb0308` |
| [admission.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/admission.json) | 1,462 | `013ad7363bc206bc7b0f5609a88139cf08babeca3f23cf5fe1c3448d90fa67c4` |

## 待闭场的事实与证据

| 项目 | 必须补齐的实际事实 |
| --- | --- |
| 背景目录迁移 | 复制完成时间、最终文件/字节清单、内容验证、联接切换、旧 C 副本处置及错误/重试原件 |
| 背景 worktree 修复 | 精确迁移根的 repair、common-dir、HEAD/status 和未提交内容读回；后续直接 D 路径合同仍按各自入口验收 |
| Defender 新路径 | 已迁移项目 EXE 的精确来源/清单、实际新路径登记及设置读回范围，未完成项如实保留 |
| 最终容量与交付闭账 | C/D 结束观察时间、free、实际删除/分配量、预留/配额结算及汇总回执；空闲差额不排他归因本次迁移，实际提交与 CI 终态另记 |

上述事实未收齐前，本页整体状态保持 **IN_PROGRESS**。
