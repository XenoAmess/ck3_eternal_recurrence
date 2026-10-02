# 独立发布计划

本产品由用户明确要求分别发布；主执行者统一协调 Steam 与账号资源。本工作包不自行上传。

## 产品身份与来源

拟发布名：公国／王国／帝国法理征服（XenoAmess维护版）。上游 `3600021457` 只作来源身份，新物品 ID 尚未创建。canonical descriptor 不能含 `remote_file_id`；新 ID 只保留在用户目录外层 `.mod` 及构建 manifest。发布文案必须致谢白绮并链接原作；授权说明须依据本产品实际许可，禁止借用其他产品的授权声明。

## 前置交付

源码 diff、功能分析、适配计划、静态与 exact-build 实机报告、冻结正式 commit／tag、deterministic staging／ZIP 与 manifest。正式上传只来自产品构建器 allowlist 输出；单独 docs、tools、夹具和原始来源不入包。

## 发布闭环

1. 完成三档 CB、负路径和并发战争矩阵，确认 exact runtime hash；按仓库发布策略完成简中／英文与其他发布语言审阅。
2. 准备 Workshop 完整描述、主视觉、initial baseline Change Notes 和永久 changelog 草稿；冻结 Change Notes 字符数、行数、SHA-256。
3. 对冻结 commit 建正式版本 tag；从该身份构建，无 remote ID 的上传 staging。
4. 新建本维护版物品，并把正式 staging 上传；保存 `EResult`、新 item ID 与 receipt。不能凭上传 API 成功宣称发布已完成。
5. 匿名读回公开标题／描述／可见性和目标 Change Notes entry；规范化后全文与冻结文本精确一致。
6. 干净取得订阅缓存，按正式 manifest 全文件验证，canonical descriptor 若被上传器添加 ID 则重建 staging 恢复无 ID 正式树。
7. 联网任务完成后立即恢复离线，保留新鲜离线画面；将实际发布事实写入 `docs/release-changelogs/de-jure-conquest/<version>.md`，提交／推送 `master`。
8. 本 mod `docs/` 保存完整发布报告与根 changelog 链接。全部交付物齐备后才标记发布完成。

首次维护版发布没有上一公开维护版本，必须写 `initial baseline`；不能用上游更新时间冒充维护版上一版本。
