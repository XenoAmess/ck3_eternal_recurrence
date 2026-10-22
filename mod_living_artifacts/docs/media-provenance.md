# 发布图片来源

封面为内置 imagegen 生成的原创宣传概念图，**不是实机截图**。项目消费文件是 [thumbnail.png](../thumbnail.png)，512×512 PNG，458,517字节，SHA-256 `84bdafacfef39c6fc4c9819401da70e1bacf70dc6eaf2dc6c0a866c32815dde3`。原图保留于生成工具默认目录；仅使用官方 [ImageMagick便携版](https://github.com/ImageMagick/ImageMagick/releases/tag/7.1.2-32)等比导出、去元数据和PNG压缩，不添加游戏界面或伪造实机内容。

完整生成提示词：

> Use case: stylized-concept. Asset type: square Steam Workshop cover for a Crusader Kings III fantasy mod titled Living Artifacts. Make a polished medieval dark fantasy oil painting: one ancient royal sword in a stone reliquary, its silver blade subtly alive with a single luminous crimson eye and fine vein-like red gold patterns, the pommel and crossguard worn noble gold. A crown and a mail gauntlet partly visible in the deep background suggest personal royal equipment. Elegant, eerie, dangerous, realistic materials and painterly detail, restrained crimson light against charcoal shadows. Strong readable sword silhouette, centered composition for a small square thumbnail. Exact large title near bottom: 活武器. Small subtitle under it: LIVING ARTIFACTS. No other text, no logos, no watermark, no game interface. This is promotional concept art, not a screenshot. Square format.

本次导出机器 `pc-20260924rtuf-f11af23c08`，UTC `2026-10-21T20:00:31.511524+00:00`，原始回执 `D:/workspace/ck3-living-artifacts-20261022/media/thumbnail-export.json`。工具包SHA为`1fdfe4558dcf17a72ff5f721b987a86949e1bcde3d53a70ce2b39c84f8815325`，原图SHA为`7f8f65648994719a52d569c3ef8d7bcf82ebd012726f61da67a463739c0053fb`。

用户要求的实机图属于独立交付项；须从通过准入的真实CK3窗口取得，绑定machine/run/PID/游戏版本与加载manifest，不能把本封面计入。Workshop additional previews实际上传及匿名下载回读的顺序、像素与来源将在完成后追加；目前没有 Workshop 上传事实。

已取得并逐字节归档一张[真实库存原图](evidence/r2-inventory.png)，1920×1080、2,520,629字节，SHA `48abbf50c049b99ffcd39e9df50b9f8716eafb76e2cd1f4c0e6b8ace8a25b020`。来源机器 `pc-20260924rtuf-f11af23c08`，实际拍摄时间 `2026-10-21T21:44:43.973072Z`，R0002/PID10924/generation1，CK3 1.20.0.4/build25734779。保存了[原 capture 回执](evidence/r2-inventory.capture.json)和[加载来源、归档及直接审阅记录](evidence/r2-inventory.provenance.json)。没有裁切、重绘或修改像素。

该图显示英语测试夹具创建的活武器目标与四档喂养材料，拍摄时武器槽仍为空。它只作为开发测试证据；不能宣传为自然获得、成长通过、正式中文版界面或完整验收通过。R2 后续装备的通过结论来自独立原生读回，见[运行记录](runtime-r2-issues.md)。

新增[中文库存原图](evidence/r6-inventory.png)，1920×1080、2,412,637 字节，SHA `4c2dea1d1d52aee5cae5282258a083181b0d5ef24867233564e61ea28968b2f1`。`machine_id: pc-20260924rtuf-f11af23c08`，原始拍摄时间 `2026-10-22T05:34:38.847608Z`，R0006/PID11856/generation1，实际 CK3 1.20.0.4/build25734779，冻结源码 `f5c9b83d274b3e823b4160a9cc62851cc35becc2`。保存[原 capture](evidence/r6-inventory.capture.json)及[实际来源索引](evidence/r6-observation-index.json)，客户区由 Win32 实际读回为 1800×980。像素逐字节复制，未裁切或重绘。

R6 图显示中文测试夹具的目标与四档材料，拍摄仍在实际装备之前；槽位 3 的后续装备依据来自原生提交 121 与独立读回。该图仍只作开发实机证据，不能当作自然获得、成长或完整功能验收图。该场第五次日推进失败且由运行器终止，正常退出未通过，见[R6 报告](runtime-r6-native-day-failure.md)。

2026-10-22 追加：R6 图片已[上传 GitHub 并可匿名下载](https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/006d22d6e75744b1ab6886119217e2a00372d11c/mod_living_artifacts/docs/evidence/r6-inventory.png)。来源机器 `pc-20260924rtuf-f11af23c08` 于 `2026-10-22T06:30:30.907552Z` 实际匿名下载，HTTP 200，字节数与 SHA 均和原图相同，回执 `D:/workspace/ck3-living-artifacts-20261022/environment/r6-image-public-GitHub-readback-a01.json`。尚未上传 Steam additional previews。

同日归档更正：提交 `006d22d6e75744b1ab6886119217e2a00372d11c` 中 capture JSON 经 Git 文本换行归一化成为 792 字节；原始 capture 是 815 字节，JSON 字段相同。保留[该次归一化副本](evidence/r6-inventory.capture.git-normalized-006d.json)，从仍保留的原始 capture 恢复[815 字节原件](evidence/r6-inventory.capture.json)，并增加 Git 字节保真规则。完整两组 SHA、原始来源和追加时间见[索引的 correction 记录](evidence/r6-observation-index.json)。截图像素未发生变化。
