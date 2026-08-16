# Steam 创意工坊发布（PDX 启动器上传器）

2026-08-17 首次发布实测（启动器版本 2026.10-rc.1）。全部结论来自启动器日志
（`%LOCALAPPDATA%\Paradox Interactive\launcher-v2\logs\launcher-YYYY-MM-DD.log`）逐条验证。

## 物料清单

| 项 | 位置 | 要求 |
|---|---|---|
| 外层 .mod | `Documents\Paradox Interactive\Crusader Kings III\mod\<name>.mod` | 含 `path=` 指向 mod 本体；上传后启动器自动写回 `remote_file_id` |
| 内层 descriptor.mod | mod 本体根目录 | **禁止含 `remote_file_id`**（见下） |
| 预览图 | mod 本体根目录，文件名固定 **`thumbnail.png`** | 启动器按约定自动找（同各 dev mod 目录）；descriptor 里同时写 `picture="thumbnail.png"` |

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

1. 改仓库内容（mod 本体）
2. 启动器 → Mods → 上传 Mod → 选同一物品（外层 .mod 的 `remote_file_id` 让它识别为更新）
3. 工坊网页：描述用 BBCode（`[h1]`/`[list]`，**不渲染 markdown**——别直接贴 README）；
   可见性默认"隐藏"，确认后改公开

## 上传内容范围

打包的是 `path=` 指向的整个 mod 目录。仓库根的 `screenshots/`、`images/`、`tools/` 不会被带上
（在 mod 目录外）。mod 内的源文件（如无损 PNG 原图）会被一起打包，注意体积与洁癖。
