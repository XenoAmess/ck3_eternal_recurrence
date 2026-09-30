# Z 盘根目录临时构建与旧工作树清理（2026-09-30）

用户在更新前冻结完成后追加授权检查 Z 盘根目录，包括 `m6-sway-goal-r0341-build`。本轮于 **21:32–21:56（Asia/Shanghai）**执行：成功移除 **131 个构建目录、28 个旧工作树，共 159 个目录**；删除前原始大小 **16,353,314,818 bytes（约 16.35 GB / 15.23 GiB）**。全部目标已确认不存在，**权限失败为 0，无须管理员删除脚本**。

清理前另存 **159 份归档、2,040 个文件**，解压内容共 1,120,748,137 bytes，压缩后 **337,247,756 bytes（约 337 MB）**。归档占用单独保留，不计入删除量；净减少约 16.02 GB，未扣除小型清单文件与文件系统开销。本轮不重复此前仓库内约 7 GB 的[清理与迁移冻结](ck3-pre-update-baseline-and-cleanup-2026-09-30.md)。

## 删除依据

- 根目录清单记录了 1,422 个一级目录。本轮处理可确认的 CK3 构建输出及旧工作树，不根据名字直接删除其他目录。
- 131 个构建目录中，114 个 CMake 项目明确为 `xar_ck3_native_bridge`；其余为已查看内容的独立 CK3 测试构建、空构建目录或构建容器。没有 `.git` 源仓库、嵌套源仓库、`.ck3` 存档或枚举错误。`m6stage2confirm_build` 的自定义 CMake 项目也核实了其引用的 CK3 activity stage2 原生测试源码。
- 用户举例的 `Z:\m6-sway-goal-r0341-build` 原占用 2,330,536 bytes，含 51 个文件，主要是 `.obj`、测试程序和 Python 缓存；其中 PR 说明已归档。该目录现已删除。
- 根目录另有 111 个本仓库的登记工作树：79 个干净且 HEAD 已合并到冻结的 `origin/master`（`c69260e65b63bf8f8b8ae42e3aee8f2a68561660`），24 个 HEAD 未合并，8 个有未提交/未跟踪内容或状态读取问题。只删除其中超过七天、已合并且干净的 28 个旧 P2 工作树；删除前另查没有存档、录像、音频或 dump。使用 `git worktree remove` 同时移除登记，提交和分支历史仍保留。

删除的旧工作树如下；各自完整 HEAD、大小与判断依据在机器清单中：

```text
p2r119s p2s10s p2s119 p2s120 p2s121 p2s122 p2s123
p2s125 p2s126 p2s127 p2s128 p2s130 p2s131 p2s133
p2s135 p2s136 p2s137 p2s139 p2s140 p2s141 p2s142
p2s143 p2s144 p2s145 p2s146 p2s147 p2s148 p2s149
```

保留其余 51 个干净工作树、上述 32 个未满足条件的工作树，以及其他候选运行现场、`native_state`、存档、live/失败证据、源码投影和游戏/工具安装目录。近期工作树可能仍用于现有现场；源码目录与 live 归档不能仅凭带有 `m6`、`candidate` 或 `tmp` 就认定为可丢弃。当前仓库已有修改、用户编辑过的旧管理员脚本也保留。

## 归档与清单

本地根目录：`Z:\ck3_mod_rewrite\artifacts\cleanup\2026-09-30-z-root`。大体积归档和清单留在本机，不提交 Git。

| 文件 | 内容 |
|---|---|
| `root-inventory.json` | 原始一级目录清单与构建配置来源。 |
| `build-assessment.json`、`build-candidates.json` | 构建目录的类型、来源、大小和删除依据；131 个最终目标。 |
| `worktree-inventory.json`、`worktree-assessment.json` | 登记、HEAD、冻结的合并基线、保留原因。 |
| `old-worktree-content-assessment.json`、`worktree-candidates.json` | 28 个旧工作树的内容检查与最终目标。 |
| `retained/`、`retained-materials.json` | 每个原目录的 `.tar.gz`、成员 size/SHA-256、归档 SHA-256 与原工作树 HEAD。 |
| `cleanup-result.json` | 159 个实际删除结果、原始大小和 UTC 完成时间；失败数为 0。 |

关键索引 SHA-256：

```text
build-candidates.json     3cbed88adecfa537a53509aabf877ffc37e9d8ba572115a62950efc4b4fb320d
worktree-candidates.json  ff7770c38756ed19cb5292ebc0ff7a55ca00f4bd6f7a47a23b8a7d5501837479
retained-materials.json   1268fc87fcf9d7a465722431b49d8c04a5edb9fb590390abebb1ee6a88546cca
cleanup-result.json      8b947f8e9fd5c341febbbafb71c1e52c8ea97b4072b4b66318a794d972f1986f
```

[`archive_ck3_cleanup_materials.py`](../tools/archive_ck3_cleanup_materials.py) 保存 DLL、PDB、bridge/injector EXE、配置、日志、PR 文本与源码片段；工作树的已跟踪源码由 Git HEAD 保留，另存其中未跟踪/ignored 的有价值文件。可重建的 `.obj`、测试 EXE、`.lib` 和 Python 缓存没有保留。每份归档写入后重新读取，所有成员 hash 均与原文件读取时的 hash 一致，归档本身也记录 hash。

需要恢复旧工作树时，按 `worktree-candidates.json` 的 HEAD 用 `git worktree add --detach <新目录> <HEAD>` 重建，再按需解压相应 `retained/worktree-*.tar.gz`；构建记录可从 `retained/build-*.tar.gz` 提取。本轮未实际演练恢复或运行已归档 DLL；旧 DLL 的 exact-build 限制仍适用。

[`cleanup_z_root_ck3_outputs.ps1`](../tools/cleanup_z_root_ck3_outputs.ps1) 消费本轮候选和已校验归档索引，只接受 `Z:\` 的明确一级子目录；普通构建使用 `Remove-Item -LiteralPath`，工作树使用 Git 删除。若实际失败，才输出包含失败绝对路径的独立管理员脚本。本轮未提权、未修改 ACL，没有失败目标，也没有改动上一轮用户编辑的管理员脚本。

## 验证与后续

本轮验证为实际归档写入/读取 hash、真实删除结果、159 个目标不存在、PowerShell AST、BOM 和文档/diff 检查。没有运行 CK3、重建 bridge、重跑 gameplay 测试或新增 live artifact，MCP readiness 与新版本兼容状态不变。

任务提交信息为 `Clean obsolete CK3 temporary directories from Z drive root`，推送到 `origin/codex/mod-shiren-import`；可用 `git log -1 --format=%H -- docs/z-drive-root-cleanup-2026-09-30.md` 查询专属提交。更新后仍从[迁移计划](ck3-update-migration-plan.md)的 M0 新 build 指纹与差异表开始。
