# Steam 创意工坊发布（PDX 启动器上传器）

2026-08-17 首次发布实测（启动器版本 2026.10-rc.1）。全部结论来自启动器日志
（`%LOCALAPPDATA%\Paradox Interactive\launcher-v2\logs\launcher-YYYY-MM-DD.log`）逐条验证。

## 物料清单

| 项 | 位置 | 要求 |
|---|---|---|
| 外层 .mod | `Documents\Paradox Interactive\Crusader Kings III\mod\<name>.mod` | 含 `path=` 指向 mod 本体；上传后启动器自动写回 `remote_file_id` |
| 内层 descriptor.mod | mod 本体根目录 | **禁止含 `remote_file_id`**（见下） |
| 预览图 | mod 本体根目录，文件名固定 **`thumbnail.png`** | 启动器按约定自动找（同各 dev mod 目录）；descriptor 里同时写 `picture="thumbnail.png"`；**< 1MB**，超限日志 warn "too large. Skipping."（上传照常成功，但预览图被静默跳过），约 900×500 PNG ≈ 700KB 是安全规格 |

## 血泪坑（全部实测复现）

### 1. 预览图约定：`thumbnail.png` 在 mod 根目录

启动器（含工坊预览图）认的是 mod 根目录下名为 `thumbnail.png` 的文件——这是 PDX 系惯例，
本机其他 dev mod（pod_greedy_head_of_faith、more_tenets_slots 等）全是这个布局。
自定义文件名/只写在 descriptor 里 → 工坊页预览图保持默认占位图，且无任何报错提示。

### 3. `remote_file_id` 只能在外层 .mod，不能进内层 descriptor.mod

首次上传只**读**内层 descriptor，带什么都能过；**更新**上传时启动器要回写内层
descriptor（"Updating first found mod descriptor in directory"），其校验器见到
`remote_file_id` 直接拒绝：

```
Publishing mod to Steam failed: Saving descriptor.mod in mod sources failed:
... Loading mod descriptor failed: Mod descriptor validation failed
```

排查方法：搜启动器日志 `Failed to publish mod`，错误链末尾就是真因。
（同理，descriptor 的 BOM 读路径能容忍，但回写路径不想赌，保持无 BOM。）

## 标准流程

1. 运行 L0：`py tools/validate_static.py`、计分 reference vectors 和
   `py tools/build_release.py --check`。这些步骤不会启动 CK3。
2. 开发候选运行 `py tools/build_release.py`；正式版本先保证 clean worktree 且 HEAD 有与 descriptor 一致的 `v<semver>` tag，再运行 `py tools/build_release.py --release`。1.0.0 输出 staging、`-v1.0.0.manifest.json` 和 deterministic `-v1.0.0.zip`，命令同时打印 manifest/ZIP SHA-256。
3. 发布前把用户目录外层 `.mod` 的 `path=` 临时指向上述 staging，保留其
   `remote_file_id="3784706360"`；不要把该字段写入 staging 内层 `descriptor.mod`。
4. 启动器 → Mods → 上传 Mod → 选同一物品。Steam 上传源必须是 staging，不能是仓库 mod 源目录。
5. GitHub 候选发布附加同一次构建的 `.zip` 和 `.manifest.json`；记录 commit、manifest SHA-256
   与工坊物品 ID，使 GitHub 与 Steam 使用同一 staging 内容。
6. 上传后把用户目录外层 `.mod` 的 `path=` 恢复为开发目录，避免后续游戏误加载旧 staging。
7. 工坊网页：描述用 BBCode（`[h1]`/`[list]`，**不渲染 markdown**——别直接贴 README）；
   可见性默认"隐藏"，确认后改公开。
8. Steam 刷新缓存后运行 `py tools/build_release.py --verify <workshop-cache> --manifest <versioned-manifest>`，要求逐文件大小/SHA-256 完全一致，再发布 GitHub draft 与工坊可见性。

## 上传内容范围

启动器会上传 `path=` 指向的整个目录，所以正式路径必须指向 release staging。
`tools/build_release.py` 只允许根目录的 `descriptor.mod`、`thumbnail.png`，以及
`common/`、`events/`、`gfx/`、`gui/`、`localization/` 内明确允许的 CK3 文件类型；不会复制
mod 内 `tools/`、仓库文档、`__pycache__`/`.pyc` 或源素材。manifest 不放进 staging，避免改变
Steam 实际内容；它作为旁置追溯物料与 ZIP 一起发布。

构建器从同一开发树生成 production-only 投影：明确排除 selftest effect、死亡探针事件/on_action/effect 与
trait bridge GUI，并剥离混合文件中的 `XAR_ACCEPTANCE_ONLY` 区域；`XAR_RELEASE_ONLY` 注释行在 staging
中展开为生产逻辑。构建会扫描所有运行文本，任何 selftest/test flag/marker 或 marker 注释残留都直接 RED。
生产 smoke 场景也会先生成此投影，再 `/MIR` 到工坊缓存实机运行，因此不是只做文本检查。
