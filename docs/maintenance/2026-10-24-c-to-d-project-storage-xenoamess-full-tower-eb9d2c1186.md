# 项目工作目录从 C 盘迁至 D 盘（2026-10-24—25）

`machine_id: xenoamess-full-tower-eb9d2c1186`。完成时间：`2026-10-24T17:08:35.793001Z`（北京时间 10 月 25 日 01:08:35）。
状态：**STORAGE_MIGRATION_AND_ACTIVE_PATH_REGISTRATIONS_COMPLETE_WITH_RECORDED_LIMITS**。

**C 盘最终可用 186.420 GiB，起始为 7.517 GiB；D 盘最终可用 599.019 GiB。** 本次完成 43 个项目根目录迁移，
原清单共 **3,095,167 个文件、190,454,212,290 B（177.3743 GiB）逻辑量**。43 份退役 C 载荷均已不存在，原 C 入口均准确联接 D 盘目标。
本状态表示目录迁移及本轮已识别活动路径注册完成；Defender、官方 CI、历史合同和证据覆盖范围的限制在下文分别保留。

## 最终位置与容量

| 用途 | 实际载荷位置 | 根数 | 原清单文件数 / 目录数 | 原逻辑字节数 | 内容哈希文件数 |
| --- | --- | ---: | ---: | ---: | ---: |
| 背景源码、构建、冻结来源和证据 | `D:/codex-ck3-background` | 1 | 2,870,504 / 198,946 | 117,061,683,398 | 5,196 |
| 原 `XarAutoplayer*` 状态和场次 | `D:/ck3-state/<原目录名>` | 42 | 224,663 / 1,722 | 73,392,528,892 | 77 |

旧 `C:/codex-ck3-background` 与 `C:/Users/xenoa/AppData/Local/<原 XarAutoplayer 目录名>` 保留目录联接，
不另存一份 C 盘载荷。`final-root-bindings.json` 逐根记录原身份、新目标和联接身份，43 项均确认旧实体 absent、D 目标准确。
文件总数来自 Git 管理路径修复前的迁移清单；后续 Git locator/config 的明确变更单独记录，不改写冻结 runtime manifest 和历史来源。

`migration-final.json` 的起始 C 可用量为 **8,071,397,376 B**（`2026-10-24T14:40:54.393022Z`），
最终 C 为 **200,167,440,384 B**、D 为 **643,191,857,152 B**（完成时刻）。早期 15:45 的 C 盘 71.39 GiB 是中途快照。
空闲差额包含系统和并发变化，不能排他归因本次迁移；`allocated_bytes_or_null=null`，逻辑长度不冒充实际分配量或物理释放量。
本机 C/D/Z 经 `GetDiskFreeSpaceW` 实读分配单元均为 4,096 B，也不据此推算精确物理回收量。

历史背景构建转到 C 的明确原因是当时 Z 盘容量不足，见 [2026-W41 记录](../autonomous-agent-progress/weekly/2026-W41.md)
和[当时的 sparse lane 说明](../ck3-native-ai/combat-phase-warmonger-predicate-12003.md)。状态目录来自用户隔离默认 `%LOCALAPPDATA%/XarAutoplayer`。
本机 D 是机械盘，本次容量迁移不构成性能改善结论。

## 数据验证与旧载荷清理

背景复制于 `2026-10-24T16:19:46.798998300Z` 完成；内层 Robocopy exit **1** 为正常复制结果，协调者读回外层 wrapper exit **0**。
独立完整根验证于 `16:46:54.251328300Z` 完成，结果 **VERIFIED**，最终原 Robocopy `/L` exit **0**。
全清单按相对名称、大小、完整 100 ns FILETIME 及额外条目核对，错误 0、`skipped_reparse=0`；关键配置及 MOD/EXE/DLL/PYD 等
共 5,196 文件、2,487,128,701 B 做内容哈希。状态清单错误也为 0、`skipped_reparse=0`，内容哈希覆盖 77 文件、1,268,005 B。
其余文件没有全量 body hash；ACL、备用数据流和旧原生文件身份不在 `/COPY:DAT` 验证范围。背景整根验证实际耗时 1,552.4015783 秒。

`2026-10-24T16:49:05.432379Z` 完成背景 C→D 联接切换，原实体移至 `C:/codex-ck3-background.c2d-retired-20261024`。
随后的删除进程 exit **0**，最终 remove 回执为 **REMOVED**：准确删除 2,870,504 文件、198,946 目录，错误 0、保留 reparse 0。
[background-migration-data-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-migration-data-final.json)
确认旧背景实体 absent；[background-ledger-integrity.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-ledger-integrity.json)
确认 gzip footer/CRC 和 2,871 个 checkpoint 批次计数完整，最大成功文件增量 1,000，最终成功文件数 2,870,504。
该检查没有重新解析全部逐文件 JSON 语义。状态清理的另一份中断日志缺口仍按下文保留。

## Git 与活动路径注册

[background-git-repair-execution.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-git-repair-execution.json)
记录必要 alternates locator 更新和 `git worktree repair`，于 `17:03:05.298712Z` 完成。
后继 `background-git-status-after.json` 于 `17:05:30.872513Z` 确认 **245/245** 条 Git 检查 GREEN：
HEAD 全部吻合、porcelain 状态输出逐字节匹配基线，核对期间 HEAD/index 元数据变化 0。**5 个原有 dirty 工作树照实保留**，没有为取得 clean 状态丢弃改动。
245 条包括关联外部工作树的定位核对，不能称作 245 棵树都被搬盘。

`background-git-local-storage-policy.json` 对修复计划内 **39 个独立 common-dir** 写入并读回 **117 项**本机设置：
`xar.projectForbidSystemVolumeBulk=true`、`xar.projectStorageRoot=D:/codex-ck3-background`、
`xar.autoplayerStateRoot=D:/ck3-state/XarAutoplayer`。范围是这些已核对项目仓库的可变本地配置，没有改写源码、runtime 或冻结 manifest。

本机用户配置已将 state、background 与项目临时根指向 D；后续仍显式传 `--state-dir`、`--userdir` 和构建输出根。
现有 `ck3-causality` MCP 的 state/environment 路径已更新，项目专属 `TEMP`/`TMP` 为 `D:/ck3-state/tmp`；
实际登记 argv+env 完成 initialize、list 和历史静态知识复验，返回 **122** 个工具，知识响应保持且无错误。
原 profile 字节保持（SHA-256 `09aa8a538949355d4924a21fe27ed88fcd77eff7d4d4582a4e01ee1d4ef8110e`）。
这些是 `mcp-scoped-environment-verification.json` 的静态范围，没有启动、attach 或操作游戏，也没有重新 prepare profile。

`live-guard-verification.json` 的四个真实只读探针全部符合预期：当前进程没有新的用户环境 forbid flag，仍能通过 Git-local fallback
拒绝 C 实体输出，允许 D 路径及两种 C→D 兼容联接路径；四项均 `no_output_created=true`。
有限外部核对覆盖 207 个计划任务、35 个 Run/RunOnce 值、909 个服务 ImagePath，以及 90 个外层 mod descriptor，
均无匹配、无读取错误；探测路径未发现启动器数据库，未查询其文本列。没有展开间接脚本，不据此声称所有外部注册或所有机器均已覆盖。

## 容量闭账与长期放置偏好

`reservation-release.json` 已将本轮 **256 GiB** 迁移预约从 274,877,906,944 B 核销为 **0 B**。
`reservation-release-adoption.json` 确认 CAS 实际采用，storage revision **2**，临界区持锁 **0.000955300172790885 秒**。
预约核销不是额外释放 256 GiB 硬盘。

`machine-storage-profile-final.json` 的迁移专用 quota override 已关闭，`quota_overrides=[]`，未来重型写入须按
[通用存储策略 1.0.0](../storage-retention-policy.md)做新鲜准入，不能复用此次配额或旧空闲快照。
七日迁移配额及审计资料到期不撤销用户的持久偏好：**项目大体量输出避开系统盘，直到用户明确撤销；数据盘空间不足时不得自动回退 C 盘。**
本轮没有修改全局 `LOCALAPPDATA`、`TEMP`/`TMP` 或其他项目设置。D 盘仍保留本机 64 GiB 系统增长预算。
最终审计/机器映射复核时间为 `2026-11-23T17:00:00Z`；迁移不刷新底层资产寿命，不声称已经部署全机或跨机自动 GC。

## 保留的实际边界

- **Defender D 路径登记未完成。** 本轮仅核对三个归档 EXE 的 C/D 字节相等，不是完整 EXE 清单；旧 File API/实际绝对 argv 来源
  不满足现有 collector 合同。当前非管理员且 broker 缺失，没有 UAC/Add 或新 native EXE 构建，不能声称 D 路径已排除。
  后续新构建沿既有 hook 登记，详见[本轮 Defender 专题](../ck3-native-ai/project-exe-defender-exclusions.md#2026-10-24-c-到-d-迁移追加候选字节已核对登记尚未开始)。
- **完整 Official Runner CI 为 RED。** 守卫提交 `4ead5f6366a38a4f859ccdc82daada27d0a14670` 的
  [run 40108917267](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40108917267) 在来源机器
  `runnervmdaln5-5f47da6a04` 的 bootstrap 阶段执行 632 项，2 failure、4 error、0 skipped；守卫自身 10/10 通过。
  仅 Canonical 负例已在父 run 实际复现；另两组为缺失 `vctip.exe` 输入和 Unicode 参数断言，父 run 未到达它们，不能一并追认为旧失败。
  **full reactor 和 actual HTTP consumer chain 均未执行**。归因见 [ci-attribution.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/ci-failure-40108917267/ci-attribution.json)
  （18,552 B，SHA-256 `6fdf52913d1d7fdd63a2eccf7fed7efa4d5f90541a1fe549debed26d9b156d7a`）；没有修无关 CI 或重跑测试。
- **本地验证范围有限。** `2026-10-24T15:26:42Z` 的[验证回执](D:/ck3-state/storage-guard-verification-publication/VERIFICATION.actual.json)
  记录默认 `mvn` 3.10.0（当时 home `C:/apache-maven`）、JDK 21.0.10（`C:/jdk-21`）；
  完整编译 76 个生产和 94 个测试源码，`-Xlint:all -Werror`，只选测 4 类共 61 项，全部通过、零跳过。
  这些机器/路径是观察事实，不锁定未来 Maven 命令；选测通过不替代失败的完整 CI。
- **状态删除日志有 453 条不可恢复记录。** 旧慢工具完成 4 根后主动中断（exit 15），原未闭合 gzip 保留；
  完整前缀仅恢复 1,000 INTENT 和 1,000 DELETED，另外 453 条无法从日志复原，没有补造记录或原生身份。
  新批次重新观察剩余原件，最终 42 个状态旧实体均 absent；这不等于存在完整逐文件删除日志，详见
  [state-interrupted-ledger-closure.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/state-interrupted-ledger-closure.json)。
- **迁移不授予游戏资格。** 没有执行新的 Game/profile preparation、rebind、continuity reducer 实机接续或 CK3 业务验收。
  原合同和历史 SHA/结果保留，新物理路径/身份需在后续实际使用时走正常资格流程；缺少 machine_id 的旧历史仍为 unknown。

## 最终证据索引

外置根为 `Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/`；逐根清单和过程回执留在该根，
本页只保留结论和关键 pin。文件大小均为 B；SHA-256 已实际读回。

| 回执 | 大小 | SHA-256 |
| --- | ---: | --- |
| [migration-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/migration-final.json) | 3,873 | `2b83b7f63e5ec52e6d4b438b4dd545b71211bc53b0d19ec6e8e1747279ad5daa` |
| [final-root-bindings.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/final-root-bindings.json) | 59,500 | `f94bd6d82e368c9fec65f96ff8435157e777c167aa863be00d00daaba77f9b3d` |
| [background-git-status-after.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-git-status-after.json) | 11,076,407 | `2c8e335e5636586f93006e332bbeabf2a62ac8bbdce0552a9cbddd2292cedcbf` |
| [background-git-local-storage-policy.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-git-local-storage-policy.json) | 98,905 | `dfb41616af16014e20246d007440e31086a237c6bc10a4fcc6de0b2d9d425cad` |
| [background-ledger-integrity.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/background-ledger-integrity.json) | 839 | `68ead4cacd4dd0e198a0cf02c4db5c5033525f20870010b6ea0cc11197498966` |
| [machine-storage-profile-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/machine-storage-profile-final.json) | 1,900 | `72c76ba7b1d9281403c55a5b6ec2079d4137fbe88497e1f18a0b3493fcc44d2e` |
| [reservation-release.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/reservation-release.json) | 952 | `e17e202a283865d499144d08296739ca8015fb2a7e2f046c7efc76fb4e18e320` |
| [reservation-release-adoption.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/reservation-release-adoption.json) | 205 | `ec2396a1ceac0a6d23d23ca10366cd02269346bcfcf2aa172eb62278bf65538b` |
