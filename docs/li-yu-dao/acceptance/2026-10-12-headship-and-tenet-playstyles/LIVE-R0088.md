# R88：白沙代表实际接受提名，道学代表与宗主仍待验

2026-10-14（北京时间）。R88 在全新 A61 有限容量准入和本场 Steam 离线、屏幕独占证据下，从 R79 的不可变原版儒家存档启动 CK3 1.20.0.4。源存档为 69,411,120 B，SHA-256 `f91795ad026e42ca5c958a5c50af949bb103381073d1ccb34fc51d05dab24e9d`；正式候选仍是 0.1.2 的 83 文件 staging，manifest SHA-256 `c3c8a398ff97c9b1af360b642bf235a973020be6613bceb7de196eae616cb1bc`。本场没有换用不存在的 `C:/workspace/ck3-upgrade-20261008`。

原生回读玩家31254、日期原值53144328、原 `confucian_faith` Faith31、宗教9、主礼仪道学33、本人白沙礼仪174；38礼仪中2派活跃。原生宗教头衔仍不存在。基线和准备两个 cell 各为 `complete/qualified=true`，道学原生资格池有279名合格选举人、推荐候选31763（学识28），白沙候选即玩家本人（学识16）。这是当场的候选池，不等于 NPC 已接受。

ROOT 经正式决议发起制度议案，`lyd.430` 处于阶段1，实际没有实施选项，选择了生产选项“待诸方答复”。随后 ROOT 经正式“自提名本派制度议案代表”决议进入 `lyd.410`，选择实际可见的“我明确赞成所示条款”。此举提供白沙玩家代表接受本轮提名的实际路径；未提交道学 NPC 的人物互动，也未取得道学代表接受、封定名单、三分之二票、玩家同意、签署、实施或宗主头衔。制度 cell 按原时限提交 `partial/qualified=false`，`business_pass=false`；不能把两个事件 ACK 或白沙动作外推为完整制度通过。

本场的 `xar_checkpoint.ck3` 为正式议案发起前的唯一后置存档（91,608,339 B，SHA-256 `45cec41bd3ec6d2aaf0789df221e47e5a2b7466cc0cd30e274e9be08dedf39d0`）。下一场从 R79 源存档重新执行发起与自提名，不能把 R88 的白沙接受当成已保存、可直接续玩的状态。下次须通过当前原生互动向道学实际合格候选提名，取得 NPC 后验，再逐项检验封定、票、同意、签署、实施、宗主头衔及保存冷载。

正常退出独立合格：ROOT 在原始截图核对退出对话框的 autosave 复选框未勾选，经带回执的坐标映射点击“退出到桌面”；CK3 原进程 OS0、native `GREEN/cleanup_ok=true`、host 退出0，公共 `normal_close_qualified=true`。显示器恢复1024×768，keeper 完成，独占屏幕序号5762→5763精确释放，Steam 保持离线。业务 partial 不因此升级。

依据[通用存储策略](../../../storage-retention-policy.md)，闭场后只清理已按大小和 SHA-256 逐件证实的重复存档：两个与本场 `xar_checkpoint.ck3` 完全相同的 autosave/last_save，及一个与 R79 不可变源存档完全相同的本场 `restored_campaign.ck3`。三份 native 原始日志逐份压为单成员 ZIP，逐份验证解压 SHA 与原始 SHA 一致再删原始流。六个原件合计489,316,083 B，ZIP 新增4,762,027 B；保留唯一后置存档、R79 来源、原生报告与当前 shadercache。闭场四根实际逻辑量418,705,200 B，加32 MiB保守余量后的 carry 为140,333,003,724 B，低于141,327,031,211 B固定上限；A61 原1.25 GiB预约余额归零并在 `2026-10-14T06:33:42Z` 前关闭。物理空闲增长不独占归因本次清理；容量协调任务序号5764完成。下一场仍须重新申请容量、屏幕与新鲜离线证据。

本场暴露公共 case 只有事件选项，没有原生普通人物互动入口。后续源码已加入有限时、一次性 `lyd_i3b_nominate_interaction` 路径：只允许当前完整原儒家名册里另一活跃礼仪的实际推荐 AI 候选，先查询 `shown/can_send/auto_accept/ready_to_initiate`，再消费意图并提交一次，保存 pending 回执，绝不把 ACK 当成 NPC 接受。隔离单测验证候选筛选；下一轮实机仍须验证真实互动与后验。0.1.2 尚未发布；Steam 公开仍为 0.1.1 Alpha 内部测试。

外置证据根：`A61=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r88-admission-20261014-061`，`R88=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0088`，`CASE039=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-039`。历史原路径与当前可用性以 A61 精确清理回执区分。

| 关键回执 | SHA-256 |
| --- | --- |
| `R88/case-output/baseline-cell-result.json` | `b61cb2be2a62abe65f17545412079013ce109915b4e8976d55d0b3f873e3b276` |
| `R88/case-output/preparation-cell-result.json` | `6c7df4864c8c9b6097cd5121618f5d0e144e9209cc81c0fbb538ef2002effc0b` |
| `R88/case-output/institution-cell-result.json` | `feaec3658d302d2130062cf621f7c7d24ff506275cd09da34864902116df5921` |
| `R88/case-output/normal-close-result.json` | `f5eda4e44c2edde0a26ed6a2d381f643e066bfb9dda80fe18c18b50254fc1595` |
| `R88/native-report.json` | `c3ee1d296f2873424a02634b7a558a559648253dabb33f3c912c36958e3f43d2` |
| `A61/R88-SCREEN-RELEASE.actual.json` | `f2ea064d2a81450660645e0d7dadced1cba1ca91906144553d72c78819f45887` |
| `A61/R88-EXACT-RECLAIM.actual.json` | `7f6644b3384aa7bb4006e950affc2986cb6da6b68d0f25d84fa12f9e0da54242` |
| `A61/CLOSED-RESERVATION.actual.json` | `f2d1f629458320c57f38e2ede489b9df5962dd9e73ee067de6adc0cdd4589436` |
