# 独立发布计划

本产品由用户明确要求分别发布；主执行者统一协调 Steam 与账号资源。本工作包不自行上传。

当前发布输入已完成16文件静态／可复现构建及简中普通GUI、公国战争保存重载、九格72项综合语义验收。实际诊断限制、跨attempt来源及原RED见 [最终验收](cn-live-acceptance-2026-10-03.md)。生产16文件不变；下一步为冻结正式commit/tag、构建该身份staging，再由主执行者完成新物品上传／缓存／公开Change Notes／永久changelog闭环。当前没有已发布事实。

## 产品身份与来源

拟发布名：公国／王国／帝国法理征服（XenoAmess维护版）。上游 `3600021457` 只作来源身份，新物品 ID 尚未创建。canonical descriptor 不能含 `remote_file_id`；新 ID 只保留在用户目录外层 `.mod` 及构建 manifest。发布文案必须致谢白绮并链接原作；授权说明须依据本产品实际许可，禁止借用其他产品的授权声明。

## 前置交付

源码 diff、功能分析、适配计划、静态与 exact-build 实机报告、冻结正式 commit／tag、deterministic staging／ZIP 与 manifest。正式上传只来自产品构建器 allowlist 输出；单独 docs、tools、夹具和原始来源不入包。

## 发布闭环

1. 仅以简体中文完成真实游戏功能验收，确认 exact runtime hash；其他八语只完成基本格式、键与占位符规范检查，不要求语义、术语、母语审阅、翻译完成度或真实游戏验收。三档CB与未覆盖边界按最终测试报告明确记录，实际RED不得发布。
2. 准备 Workshop 完整描述、主视觉、initial baseline Change Notes 和永久 changelog 草稿；冻结 Change Notes 字符数、行数、SHA-256。
3. 对冻结 commit 建正式版本 tag；从该身份构建，无 remote ID 的上传 staging。
4. 新建本维护版物品，并把正式 staging 上传；保存 `EResult`、新 item ID 与 receipt。不能凭上传 API 成功宣称发布已完成。
5. 匿名读回公开标题／描述／可见性和目标 Change Notes entry；规范化后全文与冻结文本精确一致。
6. 干净取得订阅缓存，按正式 manifest 全文件验证，canonical descriptor 若被上传器添加 ID 则重建 staging 恢复无 ID 正式树。
7. 联网任务完成后立即恢复离线，保留新鲜离线画面；将实际发布事实写入 `docs/release-changelogs/de-jure-conquest/<version>.md`，提交／推送 `master`。
8. 本 mod `docs/` 保存完整发布报告与根 changelog 链接。全部交付物齐备后才标记发布完成。

首次维护版发布没有上一公开维护版本，必须写 `initial baseline`；不能用上游更新时间冒充维护版上一版本。

## 2026-10-03发布准备复核

完整说明与BBCode已对照最终源码复核，现仍为草稿；三档费用、玩家限定、独立新物品、胜利范围、战败赔款条件与存档限制均明确。九语状态为format-certified，未新增实机或发布事实。最终canonical LF运行输入的 [16文件静态报告](release-static-2026-10-03-R0002.json) 已精确另存，旧报告保留；[文案复核说明](release-documentation-review-2026-10-03.md) 记录草稿冻结和仍待交付的发布层事项。

2026-10-03后续用户明确修正验收语言：只用简体中文做真实游戏验收，英文及其他七语只做基本规范检查。现有英文R0002调试证据保留，不计入简中签核，不再设置后续多语言实机门禁。历史R0002矩阵RED与R0005-CN夹具准备见 [记录](matrix-native-eligibility-red-2026-10-03.md)；后续简中综合验收已完成，发布闭环仍待完成。

## 2026-10-03 正式发布追加记录

维护版新Workshop ID为 [3812510217](https://steamcommunity.com/sharedfiles/filedetails/?id=3812510217)，版本1.0.0。中文实机、正式构建、完整Change Notes匿名回读、实机媒体、全新订阅缓存逐文件复核与Steam离线恢复均已通过，完整事实见[发布报告](release-1.0.0-2026-10-03/README.md)。此前阶段记录和失败attempt按原样保留。
