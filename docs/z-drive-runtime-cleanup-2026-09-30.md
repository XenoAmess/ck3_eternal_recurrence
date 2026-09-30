# Z 盘旧运行现场退役与证据去重归档（2026-09-30）

状态：**完成。2026-09-30 23:06（Asia/Shanghai）实际移除 294 个旧目录及其中 23 个源码工作树登记，全部目标已确认不存在，剩余失败为 0，无须管理员操作。**

用户指出 `Z:\m6swayh3924goalfix-recovery-live-20260929` 等旧运行目录仍大量留在根目录，要求继续清理。上一轮将这些目录整体作为证据保留，清理范围不够充分：旧运行环境可以退役，存档与记录移入稳定归档后即可移除原目录。

## 本轮范围与保留依据

根目录筛选出 328 个具有 CK3 operator manifest、native-session、stage index 或 `m6` 名称的旧目录；结合内容与 Git 状态，294 个进入归档/删除清单：126 个 native state、103 个 operator 候选、26 个 stage index 目录及 39 个其他 M6 准备/测试目录。

其中 23 个目录内部含登记的源码工作树。删除前检查其内容干净、HEAD 已合并到冻结的 `origin/master`（`c69260e65b63bf8f8b8ae42e3aee8f2a68561660`），源码文件也参与归档；随后使用 `git worktree remove` 移除内层登记，再删除外层环境。

其余 34 个目录保留：24 个独立登记的工作树，9 个独立仓库或不同仓库的源码，以及 `nw-econ-h3928-wartime-readonly-candidate-20260929` 中有未合并/未提交工作的源码。逐项目录和原因见 `runtime-assessment.json`、`nested-worktree-assessment.json`。本轮发现 Steam CK3 正在运行，未关闭游戏，也未操作 Steam 安装、真实用户目录或 `%LOCALAPPDATA%\XarAutoplayer` 当前状态。

用户举例的目录原占用 **1,508,882,903 bytes**（不含 `.git` 登记文件），包含源码副本、build-native、operator-runs、state 和 tmp。其源码 HEAD 为 `8695b2860ac07ab141abf39810a9c0c284d44160`，干净且已合并；四个 78,515,535-byte 存档及准备/运行记录参与归档。文件夹名带 `live` 不代表当前环境必须常驻，也不改变其原有证据等级。

## 归档方式与旧路径映射

本地归档根目录：`Z:\ck3_mod_rewrite\artifacts\cleanup\2026-09-30-z-runtime`。归档和大型清单留在本机，不进 Git。

| 文件/目录 | 用途 |
|---|---|
| `root-runtime-inventory.json` | 初步识别的 328 个旧目录。 |
| `runtime-assessment.json`、`runtime-candidates.json` | 保留/删除依据、大小与原文件清单。 |
| `nested-worktree-assessment.json` | 内层源码工作树 HEAD、合并基线与保留原因。 |
| `build-candidates.json`、`worktree-candidates.json` | 删除执行器的明确目标输入，本轮目录类型为 `runtime`。 |
| `retained/manifests/<原目录名>.json` | 原绝对路径、每个相对路径、size/SHA-256、去重对象路径与明确丢弃的缓存/中间文件。 |
| `retained/objects/`、`retained/object-index.json` | 按内容 SHA-256 去重的 gzip 或原始对象。 |
| `retained-materials.json`、`archive-summary.json` | 每个目录的归档位置、manifest hash、内容校验及去重统计。 |
| `cleanup-result.json` | 实际删除结果、权限失败目标和完成时间。 |
| `cleanup-attempt-1.json`、`longpath-retry-candidates.json`、`retry-longpaths.ps1` | 首轮 12 个真实长路径失败与本轮成功重试的完整记录。 |
| `restore-smoke-result.json`、`restore-smoke/`、`restore-manifest-smoke/` | 存档、DLL、JSON 与 operator manifest 的真实恢复样本及 hash 结果。 |
| `space-before-delete.json`、`space-after-delete.json` | 删除期间 Z 盘可用空间读数。 |
| `cleanup-footprint.json` | 完整归档、其他索引与恢复样本的占用。 |

历史文档和 JSON 内部的旧 `Z:\<目录>` 路径仍是当时真实位置；退役后按上述同名 manifest 查找对应字节，不能再把旧绝对路径当作现存目录。归档保存原文件内容，没有改写历史 report、driver state、manifest 或 GREEN/RED 记录，也没有将旧证据升级为新版本验收。

[`archive_ck3_runtime_materials.py`](../tools/archive_ck3_runtime_materials.py) 归档存档、报告、帧/控制日志、截图/媒体、DLL/PDB、准备脚本与源码；相同内容只存一份。排除 shader/Python/pytest 缓存及 `.obj`、`.lib` 等编译中间文件，具体被丢弃文件仍登记在目录 manifest 中。本轮 `SAV...` 标头的存档使用 gzip 保存，校验基于原始文件字节。

每个唯一对象实际写入后重读，并核对原始内容 SHA-256；每个文件引用绑定原 size/hash。重建环境时 DLL 的旧 exact-build 限制仍适用，恢复归档不会自动证明游戏环境可运行。

恢复示例（只创建新的输出目录）：

```powershell
py tools\archive_ck3_runtime_materials.py restore `
  --manifest artifacts\cleanup\2026-09-30-z-runtime\retained\manifests\m6swayh3924goalfix-recovery-live-20260929.json `
  --destination artifacts\cleanup\restored-m6-sway-h3924
```

可重复传入 `--relative-file <manifest 中的相对路径>`，仅提取指定存档、报告或 DLL。恢复后的源码是原文件副本；Git 登记没有复原，需要根据清单中的 HEAD 另建工作树。

删除使用 [`cleanup_z_root_ck3_outputs.ps1`](../tools/cleanup_z_root_ck3_outputs.ps1) 的 `-DirectoryKind runtime`，每个外层目标必须是 Z 盘明确的一级子目录，内层工作树必须位于该目标内，且已有校验通过的归档索引。只对实际权限失败项生成新的管理员脚本，上一轮用户编辑过的脚本保留。

## 实际结果与验证

归档完成：原目录清单共 **147,805,022,830 bytes / 1,484,944 个文件**。保留 **386,429 个文件、98,060,452,989 bytes 逻辑内容**，去重后为 **35,117 个唯一对象、41,024,453,510 bytes 原始唯一内容**，gzip/原始对象实际占用 **5,545,752,604 bytes（约 5.55 GB）**。各目录 manifest 和其他清单另计。排除 **1,098,515 个缓存/中间文件、49,744,569,841 bytes**；失败 attempt 的报告、原始帧、控制记录与存档继续保留。

`retained/` 连同目录 manifest 和 object index 共 **5,858,838,415 bytes（约 5.86 GB）**；其他扫描清单与恢复样本单独统计。用户举例目录的 manifest 保存 10,924 个文件、1,248,832,306 bytes 逻辑内容，排除 5,176 个缓存/中间文件、260,050,597 bytes。

实际抽样恢复了 `m6-activity-h3928-confirm-candidate-20260929` 的 checkpoint、bridge DLL、JSON 与 operator manifest，全部还原 hash 通过；operator manifest 中的 source commit、checkpoint hash 与旧 EXE 绑定也成功读回。该结果只证明文件可恢复，没有启动复原环境或执行其中脚本。

实际删除 **294 个目录 / 147,805,022,830 bytes 原始大小**，23 个内层源码工作树登记也已移除，最终失败为 **0**。归档、扫描索引及恢复样本合计约 **6.13 GB**（最终删除结果等小型记录另计）。

首轮成功 282 个目录，另外 12 个在 `git worktree remove` 遇到 `Filename too long`，不是权限不足。已保留首轮 RED，并使用 `git -c core.longpaths=true worktree remove` 重试；首轮已经部分删除的源码工作树通过 `--force` 收尾，其完整源码与证据在首轮删除前均已归档校验。最终全部清完。可复用执行器已加上长路径支持，管理员清单只筛选实际 access/permission denied，避免把长路径错误交给管理员处理；本轮临时生成的管理员脚本已撤去，上一轮用户编辑的旧脚本保留。

归档完成后的删除前可用空间为 240,401,285,120 bytes，清理完成时为 391,667,388,416 bytes，整盘同期间增加 151,266,103,296 bytes。该读数包含文件系统分配及同期间其他写入的影响，起点已包含新归档占用，不能当作扣除归档前后的任务净增量。

关键索引 SHA-256：

```text
runtime-candidates.json      997a887c853b7df73bf9271871a12cb9a5a57ea57de8247a8f1fb2f874ab29a6
retained-materials.json      da9fd7ab4c23c651f57c6958831db97373d8a300c7fd98aef28af5e787e4f0fc
retained/object-index.json   83da9730e5e9ffd062881c1e2efb43d74fe79d7afd6e0c60d82225c00444c586
archive-summary.json        7001754c3c2d1755dc5a432bfb700630371e5e62c461cd7d0b15553429312201
cleanup-attempt-1.json      64727ab036db0dad81d014dcb1d0ac481df8fac5a2860ba1ef64b6bf6c866e7d
cleanup-result.json         0eadaa540c57435ced5456571b0cabb032c688cba5a77880b5333ab0bb435f63
restore-smoke-result.json    c15862b3063d738d9e4306b58b171feb0f7fd467bfb80eb58e785955d4baa316
```

验证范围为实际对象复制/重读 hash、真实文件恢复、294 个外层目标不存在、23 个内层登记已移除、脚本语法/BOM 与文档/diff。没有重复跑 gameplay suite，也没有将归档校验称为能力 GREEN。

本轮没有运行 CK3 验收、重建 bridge 或新增 live artifact；MCP readiness 与新版本兼容状态不变。任务提交信息为 `Archive and retire obsolete CK3 runtime directories`，推送目标 `origin/codex/mod-shiren-import`。此前构建目录/旧工作树清理见[第一轮根目录报告](z-drive-root-cleanup-2026-09-30.md)，更新入口仍见[迁移计划](ck3-update-migration-plan.md)。
