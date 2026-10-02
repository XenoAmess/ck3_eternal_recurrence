# 1.0.0 发布计划

状态：待实机与正式发布门；没有上传成功事实。上游 `3337428403` 只能用于注明来源，新维护版必须使用新的 Workshop ID。

## 已备齐

来源冻结、代码适配、简中／英文 L0、外置 fixture 与可复现构建已经完成；详见 [当前报告](test-report-2026-10-03.md)。预览沿用原作者 `thumbnail.png`，SHA-256 `26ce48cd711b6a6ca65661c4511f4499da3ed72b80d1bf3b855a49e65d529071`，完整原片包含 `.sai2` 留在外置原始快照，后者不进入发布树。

[Workshop 完整描述](workshop-description.bbcode) 和 [完整 Steam Change Notes](change-notes-1.0.0.txt) 是不同交付物。目前都是待冻结文案，不能以它们证明已发布。

## 剩余发布门

1. 完成正式九语候选、格式校验和必要审阅报告；保存来源locale bytes与全部 key 覆盖。简中／英文已各44 key，候选语义审阅不能用 key 数代替。
2. 静态与 build wrapper 使用 `--release-localization`，生成全新 staging、manifest和ZIP；绑定已提交的 source commit及 `change-holding-types-v1.0.0` tag。正式树不得带 `remote_file_id`、docs、tools、fixture、原片或日志。
3. 在 `1.20.0.3`／Steam build `25652598`／EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` 上执行 [实机计划](test-plan.md)。fixture 的生产effect矩阵、真实决议目标选择／执行／个人金币读回和玩家可见图分开记证据；只有自己的实际结果可以写 GREEN。
4. 核定最终描述和 Change Notes，冻结全文、UTF-8 bytes、字符数、行数、SHA-256；任何文本改动都重新冻结，不拿一行摘要替代完整说明。
5. 在最短必要 Steam 在线窗口创建新物品并上传正式 staging、预览图和完整文案。不得以原作 ID 作为更新目标，也不得把 `EResult=1` 直接写成全文公开成功。
6. 匿名读取公开 item页和 changelog页：检查新的 item ID、作者／AppID／可见性／标题／完整描述，以及目标 changelog entry ID、HTML 解码／归一换行后的完整正文、字符数、行数和 SHA-256。
7. fresh-download 新维护版缓存，按同一正式 manifest逐文件检查inventory／size／SHA；上传后另建新staging恢复无ID正式树。立即恢复Steam离线并保存新画面证据。
8. 保存本目录正式报告，在仓库统一 `docs/release-changelogs/change-holding-types/1.0.0.md` 永久保存 initial-baseline changelog，记新的ID、版本、tag／commit、兼容限制、构建／实机／公开／缓存证据；由父任务commit/push到master后才标完成。

本产品的结果与另一个法理征服维护版分别验收；其中任何一方通过不能替代另一方。
