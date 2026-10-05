# 琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版：2026-10-06 兼容版本标签修订

状态：公开元数据核对通过。Workshop [3787304042](https://steamcommunity.com/sharedfiles/filedetails/?id=3787304042) 已补充 `Compatible Version: 1.20 'Crozier'`。

原公开版本 **1.0.2**，tag `vivhite-v1.0.2`，commit `49f535dcf277243312d7e7c0b89e6985b841b01f`；其内容、验收范围与发布日期仍见[原 changelog](../../release-changelogs/vivhite-courtier/1.0.2.md)。本次仅修改 tags，不是新内容 release。

- 标签此前：`["Gameplay"]`。
- 标签之后：`["Gameplay", "1.20 'Crozier'"]`；非版本分类原字符串保持，包括实际存在的末尾空格。
- 从固定公开 commit 提取 descriptor，SHA-256 `e72d846e2ace0a6266a8a908a8aa64a3a1ad405eca15660d46cd653bdf37a04e`；仅用作外置 metadata anchor，不上传内容。
- SDK 在 `2026-10-05T16:53:00.750603+00:00` 返回 `EResult=1`，`tags_only=true`，仅 `SetItemTags` 后 `SubmitItemUpdate(NULL)`。
- 匿名回读完整 tags、右栏分类和值及 requiredtags 链接精确匹配；旧 Notes 共 3 条，entry ID、顺序、全文 SHA、字符数与行数保持。
- 公开 API 回读确认标题、描述、可见性、内容大小与内容 handle、预览 handle 等字段保持。Steam 已恢复离线，a64 已实际释放。

详细 SDK、原始 HTTP、公开回读、构建检查与离线截图 pins 见[本批永久证据](../2026-10-06-compatible-version.json)。SDK 回执 SHA-256 `52eb2791fda2d94e7bf08830035ca608385ae8503574323ad79230dbcb31e6b7`；匿名完整回读 SHA-256 `ce92f17d33bdebd1bd447d81cebb4b30a8501ba89ee4d6fea44044ceb3af6a5b`。

以后正式更新依[统一规范](../../workshop-compatible-version.md)从正式 `supported_version` 自动派生版本 tag；已有完整发布流程继续执行。
