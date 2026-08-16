# Steam 创意工坊发布（PDX 启动器上传器）

2026-08-17 首次发布实测（启动器版本 2026.10-rc.1）。全部结论来自启动器日志
（`%LOCALAPPDATA%\Paradox Interactive\launcher-v2\logs\launcher-YYYY-MM-DD.log`）逐条验证。

## 物料清单

| 项 | 位置 | 要求 |
|---|---|---|
| 外层 .mod | `Documents\Paradox Interactive\Crusader Kings III\mod\<name>.mod` | 含 `path=` 指向 mod 本体；上传后启动器自动写回 `remote_file_id` |
| 内层 descriptor.mod | mod 本体根目录 | **禁止含 `remote_file_id`**（见下） |
| 预览图 | **两个位置都要**：mod 本体根目录 + 外层 .mod 所在目录 | **JPG 且 < 1MB** |

## 血泪坑（全部实测复现）

### 1. `picture=` 按外层 .mod 所在目录解析

descriptor 里写 `picture="workshop_preview.jpg"`，启动器找的是
`Documents\...\mod\workshop_preview.jpg`，**不是** mod 本体目录。
图只放在 mod 目录里 → 上传"成功"但预览图为空（工坊页标题图黑/占位符）。

### 2. 预览图 PNG > 1MB → 整个上传失败

报错文案极其误导："将您的 Mod 上传至 Steam 时发生错误。请确认您的 Mod 文件和 Steam 凭据。"
真实原因就是图太大。JPG quality 85 约 250KB 即可。无审核环节，不存在"等审核"。

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
