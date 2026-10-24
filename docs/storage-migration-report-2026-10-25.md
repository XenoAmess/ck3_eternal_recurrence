# C 盘项目数据迁移至 D 盘报告

编制日期：2026-10-25（北京时间）。执行机器：`machine_id: xenoamess-full-tower-eb9d2c1186`。
本报告依据 2026-10-24—25 的实际迁移回执编制；容量是所列观察时刻的快照，不代表阅读时的剩余容量，也不代表其他机器。

## 迁移结论

已将 `C:/codex-ck3-background` 和本机 `%LOCALAPPDATA%/XarAutoplayer*` 的 **43 个项目根目录**迁至 D 盘，
原清单共 **3,095,167 个文件、190,454,212,290 B（177.3743 GiB）逻辑数据**。
复制和验证完成后已清除旧 C 盘实体载荷；43 个旧路径均保留准确指向 D 盘的目录联接，兼容历史引用。

迁移完成时间为 **2026-10-25 01:08:35 北京时间**（`2026-10-24T17:08:35.793001Z`）。
完成状态为 `STORAGE_MIGRATION_AND_ACTIVE_PATH_REGISTRATIONS_COMPLETE_WITH_RECORDED_LIMITS`：
目录迁移及本轮已识别活动路径登记完成，Defender、完整 CI 和历史运行资格的限制见后文。

| 容量观察 | 可用字节数 | 可用容量 |
| --- | ---: | ---: |
| C 盘迁移前，2026-10-24 22:40:54 北京时间 | 8,071,397,376 B | 7.517 GiB |
| C 盘迁移完成时 | 200,167,440,384 B | 186.420 GiB |
| D 盘迁移完成时 | 643,191,857,152 B | 599.019 GiB |

空闲量变化包含同期系统及其他任务变化，不能全部归因本次迁移。177.3743 GiB 是文件逻辑长度，
本轮没有取得完整实际分配量，不能把它写成精确物理释放量。D 盘为本机机械盘，本次没有性能提升结论。

## 原因与范围

背景目录曾因 Z 盘容量不足而放到 C 盘；依据是 [2026-W41 周报](autonomous-agent-progress/weekly/2026-W41.md)
和[当时的构建说明](ck3-native-ai/combat-phase-warmonger-predicate-12003.md)。
自动玩家原默认使用用户隔离目录 `%LOCALAPPDATA%/XarAutoplayer`，多个版本和场次又形成多个同前缀目录。
这些默认位置及持续生成的工作树、构建和运行资产，共同造成项目数据长期占用系统盘。

| 内容 | 原入口 | 迁移后的实际位置 | 原清单文件数 | 原逻辑量 |
| --- | --- | --- | ---: | ---: |
| 背景工作树、构建、冻结来源和证据 | `C:/codex-ck3-background` | `D:/codex-ck3-background` | 2,870,504 | 117,061,683,398 B |
| 42 个自动玩家状态及场次目录 | `C:/Users/xenoa/AppData/Local/XarAutoplayer*` | `D:/ck3-state/<原目录名>` | 224,663 | 73,392,528,892 B |

主源码目录继续位于 `Z:/ck3_mod_rewrite`。本轮未整体迁移用户账户、全局 AppData、全局临时目录或已安装的第三方依赖。
文件数取自 Git 管理路径修复前的迁移清单，后续 Git locator/config 的明确变更另有回执。

## 执行与验证

执行顺序为：核对机器和容量预算 → 停止精确匹配的旧路径消费者 → 复制至 D → 独立验证 → 切换目录联接 →
删除已验证的旧 C 实体 → 修复 Git 和活动路径登记 → 读回容量及配置并闭账。
本轮没有启动或操作 CK3，没有切换 Steam 在线状态，也没有改写冻结 runtime manifest 来追认新路径。

| 验证项 | 实际结果 | 覆盖范围 |
| --- | --- | --- |
| 复制清单 | 43 根完成验证 | 相对路径、大小、精确 100 ns 修改时间和额外条目；清单错误及跳过 reparse 均为 0 |
| 内容哈希 | 背景 5,196 文件；状态 77 文件 | 关键配置、MOD/EXE/DLL/PYD 等；其余文件未全量哈希 |
| 旧入口及载荷 | 43 个联接准确，43 份旧实体不存在 | 逐根目标和原生身份保存在 `final-root-bindings.json` |
| Git | 245/245 检查通过 | HEAD 和完整 porcelain 状态与基线一致，原有 5 个 dirty 工作树保留 |
| Git 本机配置 | 39 个 common-dir，117 项写入及读回通过 | 背景根、状态根和禁止系统卷大体量输出设置 |
| MCP | 实际登记参数和环境可用，返回 122 个工具 | initialize、list、历史静态知识查询；原 profile 字节保持 |
| Java 守卫本地回归 | 61 项通过，0 failure/error/skipped | 完整编译相关 76 个生产、94 个测试源码，选测 4 类；不等同完整 CI |
| 实际路径守卫探针 | 4 项符合预期，未创建输出 | 拒绝 C 实体输出；允许 D 和两类 C→D 兼容联接入口 |

背景复制的 Robocopy exit 1 是正常复制结果，外层协调进程 exit 0；最终只读复验 exit 0。
背景旧实体删除进程 exit 0，文件及目录计数吻合。245 条 Git 检查包含关联的外部工作树，不能理解为迁移了 245 棵树。
本轮未验证所有文件的 ACL、备用数据流或旧 FileID；文件身份变更的后续消费者仍须按正常流程重新取得资格。

## 已调整的登记与文档

`C:/Users/xenoa/.codex/config.toml` 中 `ck3-causality` 的状态目录及 environment manifest 改指 D 盘，
并为该 MCP 子进程显式设置 D 盘 `TEMP`/`TMP`。配置修改前的备份保存在本轮外置证据根。
项目 HTTP operator 的原连接保持；未发现需要改盘符的计划任务、Run/RunOnce 或服务 ImagePath 直接引用。

用户环境变量已写入并实际读回：

| 变量 | 本机值 |
| --- | --- |
| `XAR_AUTOPLAYER_STATE_DIR` | `D:/ck3-state/XarAutoplayer` |
| `XAR_PROJECT_STORAGE_ROOT` | `D:/codex-ck3-background` |
| `XAR_CK3_BACKGROUND_ROOT` | `D:/codex-ck3-background` |
| `XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK` | `true` |
| `XAR_PROJECT_TEMP_ROOT` | `D:/ck3-state/tmp` |

已经运行的进程不会自动刷新用户环境，因此本轮同时修改了显式 MCP 参数，并在 39 个 Git common-dir 配置本机回退值。
后续调用仍应显式提供 `--state-dir`、`--userdir` 和构建输出根。

| 仓库文件 | 本轮变更用途 |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | 固化大体量输出避开系统盘、D 盘不足不得退回 C 的长期要求 |
| [自动玩家 README](../ck3_autonomous_player/README.md) | 更新状态目录配置说明 |
| [便携 MCP 配置](ck3-portable-codex-mcp-setup.md) | 更新本机路径配置和迁移边界 |
| [分支与工作树管理](branch-management.md) | 更新工作树放置与迁移说明 |
| [Defender 排除专题](ck3-native-ai/project-exe-defender-exclusions.md) | 记录新 D 路径尚未登记的原因和后续所需来源 |
| [详细维护记录](maintenance/2026-10-24-c-to-d-project-storage-xenoamess-full-tower-eb9d2c1186.md) | 保存完整时间线、数量、验收边界和关键回执 SHA-256 |

有限外部注册检查实际覆盖 207 个计划任务、35 个 Run/RunOnce 值、909 个服务 ImagePath 和 90 个外层 mod descriptor，
没有旧路径直接匹配或读取错误。未展开间接脚本；探测位置没有启动器数据库，未取得其文本列覆盖结论。

## 后续防止 C 盘再次累积大体量数据

1. **默认位置固定到获准数据卷。** 本机新背景工作树和构建使用 `D:/codex-ck3-background`，状态和场次使用
   `D:/ck3-state`，项目临时目录使用 `D:/ck3-state/tmp`；禁止再在 AppData 下为新工作包创建真实的 `XarAutoplayer*` 大目录。
2. **Java 构建及 SDK 装配入口执行实体卷检查。** 已接入的 `ProjectStoragePolicy` 解析实际目标和联接，
   在创建大输出前拒绝系统盘实体目录；路径名称写成 C 但实际指向 D 的兼容联接按真实目标判断。
   配置按 JVM 属性、进程环境、Git-local 的顺序读取。旧工具尚未全部接入自动拦截，执行者必须先核对其输出根和峰值。
3. **数据盘容量不足时停止或回收。** 按[通用存储策略](storage-retention-policy.md)和[版本化参数](storage-retention-policy.json)
   在任务开始、重型写入前和闭场检查容量、并发预约、配额、系统增长预留及资产期限；不得自动退回 C 盘。
4. **保留期限继续生效。** 迁移不延长原资产寿命，过期资料仍按统一策略复核；本轮 256 GiB 迁移预约已核销为 0，
   临时 quota override 已关闭，不能作为下一次重型写入的准入。

这些约束已实际落到本机配置、已接入 Java 入口和仓库指令，未部署为全系统写盘封锁或全机自动 GC。
避开系统盘是持续偏好，直到用户明确撤销；审计资料到期不撤销该偏好。机器映射与本轮审计复核点为
`2026-11-23T17:00:00Z`，其他机器必须另核身份和获准数据卷。

## 未完成事项与使用边界

| 事项 | 本轮状态 | 后续处理要求 |
| --- | --- | --- |
| 旧 EXE 的 D 路径 Defender 排除 | 未登记、未验证 | 已核对三个归档 EXE 字节；缺少现有 collector 接受的 File API/实际绝对输出命令来源，且本机非管理员、broker 缺失；取得真实来源后走现有登记链，不伪造旧构建清单 |
| 完整 Official Runner CI | 守卫提交对应 run 为 RED | run 40108917267 的 bootstrap 632 项中 2 failure、4 error，守卫自身 10/10 通过；full reactor 和 actual HTTP consumer chain 未执行，不能以本地 61 项通过替代 |
| 状态清理逐文件日志 | 原中断 gzip 有 453 条无法恢复的删除记录 | 原件和缺口如实保留；恢复批次重新核对剩余源文件，最终 42 份旧实体均已不存在，不补造日志或原生身份 |
| CK3 实机和冻结合同 | 本轮未重新取得业务资格 | 未执行 Game/profile preparation、rebind 或 continuity 接续；后续使用 D 路径时须走正常资格流程 |
| 旧工具自动拦截覆盖 | 部分入口具备 | 未接入工具继续受输出位置和容量准入规则约束，不能外推为全工具自动保护 |

守卫 CI 的来源机器是 `runnervmdaln5-5f47da6a04`，与本机不同。失败归因及原报告链接见详细维护记录；
本报告记录迁移时取得的验证事实，不将其描述为当前最新 master 的 CI 状态。

旧 C 实体已经删除，不能依赖旧 C 载荷做原地撤销。后续若要再次迁移，必须从现有 D 数据重新清点、复制、验证和切换，
并重验所有路径消费者；历史引用尚未更新前保留兼容联接，不能把联接目标当作重复副本删除。

## 交付与证据

守卫及初始文档提交：[`4ead5f6366a38a4f859ccdc82daada27d0a14670`](https://github.com/XenoAmess/ck3_eternal_recurrence/commit/4ead5f6366a38a4f859ccdc82daada27d0a14670)。
最终迁移记录提交：[`7327ad4983b18923c2b6df9f54ba4634ba32ba4c`](https://github.com/XenoAmess/ck3_eternal_recurrence/commit/7327ad4983b18923c2b6df9f54ba4634ba32ba4c)。
两次均普通 fast-forward 推送；使用隔离工作树交付，原主工作目录的 HEAD、index 和既有未提交工作保持。

本机外置证据根为 `Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/`。
详细维护记录包含关键文件 SHA-256；以下为报告主要依据：

- [migration-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/migration-final.json)：最终数量、容量、状态和边界。
- [final-root-bindings.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/final-root-bindings.json)：43 个旧入口与 D 目标的逐根映射及身份。
- [registrations-and-environment.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/registrations-and-environment.json)：配置备份、参数和用户环境实际读回。
- [machine-storage-profile-final.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/machine-storage-profile-final.json)：本机根映射、卷身份、预留和持久偏好。
- [final-publication.json](Z:/codex-storage-audit/2026-10-24-xenoamess-full-tower-eb9d2c1186/migration-execution/final-publication.json)：交付提交、远端读回及原工作目录保护结果。

这些外置原件只在保留期限内提供本机证据可读性；后续如按存储策略回收，引用必须注明原件已不可读取，不能制造同名替代证据。
