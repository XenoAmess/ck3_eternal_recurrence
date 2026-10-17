# 受管录制预配置标记：小型来源包

本包用于[公共单行预防修复](../../obs-preconfigured-first-run-2026-10-17.md)。`SOURCE-PINS.json` 保存原件精确 SHA 和公共源的规范换行 SHA；这里只收259e失败、前台归属、正常关闭及启动身份小元数据，没有视频、Driver、SAVE或完整 provider 副本。

- `actual-failed.json`／`actual-foreground-observation.json`：本次 owned OBS 取得前台，守卫失败，不尝试恢复用户焦点。
- `actual-cleanup.json`：输入解绑、正常退出码0，无强杀。
- `OWNER-RETRY-READY.json`：来源方 file-only retry 资格与完整出处，不能当重试已执行。
- `future-builder-first-run.patch`：来源方窄候选，公共移植只改生成配置的该字面量，原文件其余差异不复制。
- `OBS30-SOURCE-REVIEW.json`：官方30.0.0解析到固定提交 `34ef67e2…` 后下载源码的完整 SHA 与两段窗口摘要。网页文本抽取可能重排空行，文档链接按实际 Git 原始文件行号。
- `PUBLIC-FOCUSED-TESTS.json`：真实公共函数与既有守卫的13项离线检查，不启动 OBS、Game或MCP。

旧 builder 已有 `LastVersion`、隐藏启动／托盘参数，旧启动前 INI 未保全，具体窗口／向导原因仍未知。本包不修改任何活跃配置、不追认录制成功、不授成片或30年目标信用。原件按通用存储策略复核；本跟踪源码／小记录用于复现该边界。
