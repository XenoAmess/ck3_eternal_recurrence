# 1.0.0 发布计划

状态：待本产品简体中文实机最终签核与正式发布闭环；其他八语只做格式检查，不做语义／术语审阅或实机。没有上传成功事实。上游 `3337428403` 只能用于注明来源，新维护版必须使用新的 Workshop ID。

## 已备齐

来源冻结、代码适配、正式九语候选 L0、外置 fixture 与可复现构建已经完成；详见 [当前报告](test-report-2026-10-03.md)和[正式静态R0003](release-static-R0003-2026-10-03.json)。九语格式与保护token层结果见[覆盖报告](localization-coverage-2026-10-03.json)；依用户最新指令，其他八语只检查格式，外语实机或语义／术语审阅不是当前发布要求。预览沿用原作者 `thumbnail.png`，SHA-256 `26ce48cd711b6a6ca65661c4511f4499da3ed72b80d1bf3b855a49e65d529071`，完整原片包含 `.sai2` 留在外置原始快照，后者不进入发布树。

[Workshop 完整描述](workshop-description.bbcode) 和 [完整 Steam Change Notes](change-notes-1.0.0.txt) 是不同交付物。目前都是待冻结文案，不能以它们证明已发布。

## 剩余发布门

1. 保留九语现有文件及格式／token覆盖报告，每语各44 key。仅检查BOM、header、key集合与唯一性、版本／引号／换行和保护token格式；其他八语不安排语义／术语审阅或实机。中文文案、渲染和交互在简体中文实机报告中记录。
2. 静态与 build wrapper 使用 `--release-localization`，生成全新 staging、manifest和ZIP；绑定已提交的 source commit及 `change-holding-types-v1.0.0` tag。正式树不得带 `remote_file_id`、docs、tools、fixture、原片或日志。
3. 在 `1.20.0.3`／Steam build `25652598`／EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` 上仅以简体中文执行[实机计划](test-plan.md)。fixture 的生产effect矩阵、真实决议目标选择／执行／个人金币读回和玩家可见图分开记证据；只有自己的实际结果可以写 GREEN。
4. 核定最终描述和 Change Notes，冻结全文、UTF-8 bytes、字符数、行数、SHA-256；任何文本改动都重新冻结，不拿一行摘要替代完整说明。
5. 在最短必要 Steam 在线窗口创建新物品并上传正式 staging、预览图和完整文案。不得以原作 ID 作为更新目标，也不得把 `EResult=1` 直接写成全文公开成功。
6. 匿名读取公开 item页和 changelog页：检查新的 item ID、作者／AppID／可见性／标题／完整描述，以及目标 changelog entry ID、HTML 解码／归一换行后的完整正文、字符数、行数和 SHA-256。
7. fresh-download 新维护版缓存，按同一正式 manifest逐文件检查inventory／size／SHA；上传后另建新staging恢复无ID正式树。立即恢复Steam离线并保存新画面证据。
8. 保存本目录正式报告，在仓库统一 `docs/release-changelogs/change-holding-types/1.0.0.md` 永久保存 initial-baseline changelog，记新的ID、版本、tag／commit、兼容限制、构建／实机／公开／缓存证据；由父任务commit/push到master后才标完成。

本产品的结果与另一个法理征服维护版分别验收；其中任何一方通过不能替代另一方。

R0001的harness RED、R0002的真实GUI付款与fixture diagnostic、R0003重载／干净矩阵及R0004英文过程均见[实机边界记录](live-attempt-status-2026-10-03.md)。历史英文证据不替代中文最终签核。

## R0004历史英文过程与现行范围

[R0004 报告](live-R0004-visual-route-2026-10-03/README.md) 确认英文六名称、城市说明、Trani目标及成本400；完整警告仍被tooltip遮挡，名为unobscured的末帧也不满足门禁。debug French按钮／控制台路线后HUD仍英文，分类为测试路线 FAIL，产品法语及其余六语视觉均未测，外语冷启动路线现已取消，保留该次历史失败事实。debug原版 `is_ai` trigger perspective 诊断及产品调用上下文完整保留，没有改 runtime。实际session-final与bus-release证明清理／屏幕释放；R0003 register回执误覆盖另见 [追加勘误](corrections-2026-10-03.md)。

当前仍待简体中文实机最终签核及正式上传／公开全文Change Notes／fresh缓存／永久changelog；历史R0004外语路线及英文警告截图不作为中文签核。九语格式检查保留，外语实机和语义／术语审阅计划取消。

当前验收范围以[语言验收政策](localization-acceptance-policy-2026-10-03.md)为准：**只进行简体中文实机验收；其他八种语言只做格式检查，不进行语义／术语审阅或外语实机验收。**
