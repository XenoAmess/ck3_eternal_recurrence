# CK3 更新前冻结与废弃产物清理：2026-09-30

状态：**更新前归档和本次可清理项已执行；新 build 适配待更新后开始**。实际操作从 20:25（Asia/Shanghai）开始；没有启动 CK3、执行玩法命令或重跑历史验收。

用户在迁移计划交付后授权立即执行，并追加清理废弃资料、输出权限不足目录的管理员删除脚本。本记录对应 [迁移计划第 3 节](ck3-update-migration-plan.md)。

## 冻结结果

归档根目录：

```text
Z:\ck3_mod_rewrite\artifacts\migrations\2026-09-30\pre-update
```

截至本记录，归档约 **1.475 GB、1,036 个文件**，不提交 Git；后续新增索引文件会改变总数。游戏本体复用已有完整旧安装，不重复复制。

| 材料 | 实际结果 |
|---|---|
| 游戏进程 | 开始时未发现 `ck3.exe` 或相关自动游玩 Python owner，无需停止进程；未终止其他 Python/Steam。 |
| 已保留游戏 | `Z:\Crusader Kings III\Crusader Kings III_1.19.0.6_20260604`，EXE 对应已绑定 `1.19.0.6`。 |
| Steam 当前安装 | `Z:\SteamLibrary\steamapps\common\Crusader Kings III`；冻结时 build ID `23530548`，版本 `1.19.0.6 (Scribe)`。 |
| 仓库参考安装 | `Z:\ck3_mod_rewrite\Crusader Kings III`；与前两份分别冻结，路径不能混为同一目录。 |
| EXE / 数据 | 三份 EXE 都为 `95,206,008` bytes、SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。每份冻结 15,048 个 common/events/gui/localization/history/map_data/DLC 相关文本文件；该范围内新增、删除、内容差异均为 0。未对大型纹理/音频做重复审计。 |
| 自动玩家 state | `%LOCALAPPDATA%\XarAutoplayer` 的 native-session、strategy、control、logs、profile、全部 13 个当前 save 文件与顶层状态文件已复制。保留 production projection/manifest、tutorial、设置与 DLC 配置。 |
| 真实用户目录 | 当前全部 5 个存档、顶层文件（含 last_save、tutorial 与 launcher SQLite）、logs、player、rulers、playsets backup 及外层 `.mod` 描述符已复制；未修改真实现场。 |
| 核心 native 构建 | 事件 scope、事件 window 与 production12 默认关闭 startup recorder 的三套构建保留原目录并归档 DLL/injector、可用 PDB 与 CMake 配置。其余待清理构建的 606 个关键产品/配置/日志另外归档并核对 hash。 |
| 源码 | HEAD `dcecf6296b2915968c1e838199fbfdfed32642d9`、相关 tracked 工作树与必要 untracked 源码、binary diff 已冻结；包含既有未提交工作，不冒充 clean release。 |
| capability | 保存 62 项源码声明能力及现有 native ABI/专题，明确标为静态清单；没有用新 hello 或 live query 升级证据等级。 |

复制阶段所有归档文件均核对来源/副本 SHA-256。profile 没有复制历史 crash dumps、shadercache、account 缓存；历史 runs/录像、真实用户 mod 的完整内容树和旧 `save games_bak` 保留原地，不属于本次核心恢复包。该归档是更新前恢复材料，不宣称完整镜像了所有历史日志/媒体。

## 当前可恢复存档与已知缺口

两个实际归档文件都与已归档 metadata 的 size/hash 匹配：

| 文件 | bytes | SHA-256 | 原锚点 |
|---|---:|---|---|
| `autoplayer-state/profile/save games/xar_checkpoint.ck3` | 66,594,755 | `5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F` | Character `29829`、date `53175816`、history `132`。 |
| `autoplayer-state/profile/save games/xar_episode_seed.ck3` | 63,874,889 | `46A753F02AAE87299AD9658DA898F5938C1103B251E1EF56AD29FE38E9EAF53D` | Character `29829`、date `53168784`。 |

原 `driver-state.json`、episode seed/transition、pipe 和历史命令记录按原样保存；副本中的绝对路径仍指向旧源目录，**不是直接运行用的新 profile**。恢复时复制到新的 state，然后按计划重绑 profile、重新观测 session/token，不能重放旧 inbox。

[canary handoff](autonomous-agent-progress/one-generation-canary-handoff.md) 引用的 `%TEMP%\xar-war-entry-production6b-state` 已不存在，其 `67,118,175` bytes / `12FD30A0...04F37D` checkpoint 不在本次可用材料中。现存 checkpoint 是另一真实旧 frame；不伪造缺失 state，不把它称为原 production6b canary。旧目录运行回退和任何新版本存档兼容均尚未实测。

## 清理结果与保留范围

实际移除：

- **201 个**未跟踪、超过 7 天、带 CMake 生成标记的过时构建目录，关键 DLL/injector/PDB/配置先归档；三套明确复用构建保留。
- **12 个**根目录未跟踪 `.obj` 编译文件。
- **10 个**旧 worktree：tracked/untracked 状态干净，HEAD 已包含在冻结的 `origin/master`（`c69260e65b63bf8f8b8ae42e3aee8f2a68561660`），通过 `git worktree remove` 删除，登记元数据同时移除。源码仍可从该提交历史取得。

上述成功删除项已知原始大小合计 **7,004,886,880 bytes（约 7.00 GB / 6.52 GiB）**；这是删除项大小，不是扣除新归档后的净释放量。13 个失败目录部分已删文件不计入该数字；新归档约 1.475 GB。

旧 worktree 本次审阅 110 个，仅上述 10 个满足清理条件；其余 100 个存在未提交/未跟踪工作或 HEAD 未合入冻结 master，保留。项目共有 622 条 worktree 登记，本次没有全盘删除其他盘或近期 `.task-tmp` 工作区，也没有清理分支、Git 历史、冻结 live artifact、旧游戏目录或真实用户 crash/media。

## 管理员清理脚本：13 个实际权限失败目录

脚本：[`tools/cleanup_ck3_admin_20260930.ps1`](../tools/cleanup_ck3_admin_20260930.ps1)。本次没有自动提权或修改这些目录的 ACL。请在**管理员 PowerShell**执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "Z:\ck3_mod_rewrite\tools\cleanup_ck3_admin_20260930.ps1"
```

脚本内逐项列出以下绝对路径，使用 `Remove-Item -LiteralPath`；若管理员删除仍被拒绝，只对列出的该目录执行 ownership/ACL 修复后重试：

```text
Z:\ck3_mod_rewrite\.build-combat-trace-detour-v1b-msvc
Z:\ck3_mod_rewrite\.build-combat-trace-managed-v1-msvc
Z:\ck3_mod_rewrite\.build-startup-consumer-guard-syntax-msvc
Z:\ck3_mod_rewrite\.build-startup-consumer-guard-syntax2-msvc
Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly-msvc
Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly2-msvc
Z:\ck3_mod_rewrite\.build-startup-localize-final-readonly3-msvc
Z:\ck3_mod_rewrite\ck3_autonomous_player\.build-startup-guard-production8-msvc
Z:\ck3_mod_rewrite\ck3_autonomous_player\.build-startup-guard-production8d-msvc
Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\.build-dx11-draw-guard-review-msvc
Z:\ck3_mod_rewrite\ck3_autonomous_player\native_bridge\build-msvc
Z:\ck3_mod_rewrite\_runtime\pytest-portable-normal-1789010595710
Z:\ck3_mod_rewrite\_runtime\pytest-portable-opt-1789010595710
```

## 索引、校验与更新后的入口

归档内保留以下机器可读索引；路径以归档根目录为基准：

| 文件 | 用途 / SHA-256 |
|---|---|
| `backup-files.json` | 405 个核心文件的来源、归档路径、size/hash；`114AF76E563B9C5FBD1B71D29FA43CD69C81FEED70703FA0DADBA392C684E7FB`。 |
| `retained-build-files.json` | 606 个待清理构建关键产品的来源与副本 hash；`94D2AA1294075B4101CF02DD8E22D5D9D1B4A7D081F2AC5C2A1A5107BF956960`。 |
| `metadata/source-working-tree.tar.gz` | 源码/相关工作树快照；`C75AEE3B9A48B7CA8466393CCD5F90BB504FF62445D228E0117ECBB48C775E7D`。 |
| `metadata/build-identity.json`、`game-data-*.json`、`steam-build.json` | 三份 exact build、PE/launcher/Steam 及数据指纹。 |
| `metadata/state-bindings.json`、`adapter-capabilities-static.json` | 当前 checkpoint/seed 的真实绑定及静态能力集合。 |
| `cleanup-result.json` | 213 个成功项与 13 个权限失败项；`EC622148E0ADC556854B44D13C77F7457B91EA668515A12AC84BA0ADCAAFC59B`。 |
| `worktree-cleanup-result.json` | 10 个成功 worktree、HEAD 和大小；`3FDDD4E1D4611CE90D7A4834C3A007A441E263F9AC62AACD80D90534F3E70C6D`。 |
| `worktree-inventory.json`、`worktree-cleanup-assessment.json` | 全部登记与本次具体保留/删除依据。 |

可复用采集工具为 [`freeze_ck3_migration_metadata.py`](../tools/freeze_ck3_migration_metadata.py)，用于已有核心归档后的 build/data/source metadata 冻结；它不会复制核心 state，要求已有 `autoplayer-state`，也不能代替游戏实机验收。清理执行器为 [`cleanup_ck3_obsolete_outputs.ps1`](../tools/cleanup_ck3_obsolete_outputs.ps1)，消费本轮确切 candidate 清单，管理员脚本只包含实际失败目标。

本次验证为真实复制 hash、实际 metadata capture、真实删除结果、PowerShell 语法与文档检查；未运行 CK3 或重建 bridge。下一步等待实际新 build，执行 M0 的新身份/差异表，再推进 M1/M2；无需重跑本轮冻结。

用户随后追加的 Z 盘根目录清理另记于 [2026-09-30 根目录清理](z-drive-root-cleanup-2026-09-30.md)：131 个构建目录与 28 个旧工作树、16.35 GB 原始占用、337 MB 留存归档，本轮无权限失败；与上面的仓库内清理分别统计。
