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

2026-10-22 名称需求追加后的[带星号中文库存原图](evidence/r7-star-inventory.png)：1920×1080、2,449,041 字节，SHA `6f0627796769c80eecd2d564b312c6ba8d69ca8ca37dcf650f311fe7aa7bb210`。`machine_id: pc-20260924rtuf-f11af23c08`，拍摄时间 `2026-10-22T07:36:24.839185Z`，R0007/PID10940/generation1，CK3 1.20.0.4/build25734779，冻结源码 `7559ccccf66348d9dae3b50b1cc2f40145c05df3`。库存实际显示 `★待测活武器`，四档普通材料无星号；同场严格解包的真实存档名称一致。[原始 capture 字节副本](evidence/r7-star-inventory.capture.json)和[来源、加载 manifest、实际存档及审阅索引](evidence/r7-star-inventory.provenance.json)均已保存。该图拍摄于装备前，仅证明初始测试目标的名称显示与保存，不授予成长、喂养、AI、传承或完整发布通过。

该图已[上传 GitHub](https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/10c37fa927e1df033c2d837c96f8d696ed4eadc2/mod_living_artifacts/docs/evidence/r7-star-inventory.png)。来源机器 `pc-20260924rtuf-f11af23c08` 于 `2026-10-22T07:40:16.886968Z` 实际匿名下载，HTTP 200、字节数与原图 SHA 精确一致；原始回执 `D:/workspace/ck3-living-artifacts-20261022/environment/r7-star-image-public-GitHub-readback-a01.json`。后续升级与中断失败范围另见[R7 报告](runtime-r7-star-growth-and-interruption.md)，不能仅凭截图授予整体验收。Steam additional previews 仍待实际发布时上传。

## 2026-10-24 工坊艺术与普通游玩配图

以上“未上传”属于各历史时点。`machine_id: pc-20260924rtuf-f11af23c08` 于本日实际向物品 `3825237804` 新增四张合格配图，并在正文嵌入四个 SDK 实际返回的 Steam CDN 地址，未复用 R2、R6、R7 或已撤下的 R8 夹具图。顺序、公开地址和范围见 [工坊配图索引](../../workshop/living_artifacts_screenshots.md)。

新主视觉与喂养主题图为内置 imagegen 概念美术，完整提示词、原件与导出记录保存在 [素材目录](../../promo/living_artifacts/workshop-media-wip-20261024-a01/README.md)。概念图没有冒充游戏界面。R31 的自然「★君王之杖」原屏和 R33 正常决议打开的「活武器管理」说明均来自无业务夹具的普通正式战役；全帧导出 JPG，没有重绘、拼接或裁去测试字样。

R33 原屏为 1920×1080、2781251 B，SHA-256 `2c24add09d23879d784a20e18fed0934eff01ab583817ba6bddebaed52dbe29f`；原文件 mtime 为 `2026-10-24T13:48:02.358732Z`，此处只记录文件时标，不替代单独捕获回执。PID16224、出生时间 Unix `1792847623.400076`、玩家33702、CK3 1.20.0.4/build25734779；原生步骤 `r33-confirm-manage-01` 在 `13:43:23.164431Z` 实际观察到 `xalw.12`。该图仅为管理入口说明，不展示训练、喂养、镇压付款或成长结果。R31/R33 后续失败及未获正常退出资格保持原样，图片像素真实性不授予整场业务通过。

本次两次 SDK 提交实际原退出均为 0、`steam_result=1`、`stage=complete`。匿名公开 API 的 7413 B 描述与冻结 BBCode 完全一致；四张 Steam CDN 图均 HTTP200，字节、SHA 和尺寸逐一匹配上传 JPG。实际证据及未完成范围见 [publication.json](../../promo/living_artifacts/workshop-media-wip-20261024-a01/publication.json)。旧夹具证据继续保留其开发用途，不进入本次宣传图库。

同日后继 R35 新增 [实际活物管理状态原屏](../../promo/living_artifacts/workshop-media-wip-20261024-a01/screenshots/05-living-artifact-state-r35.jpg)：1920×1080 JPEG、639336 B，SHA-256 `dadcdfef31f3ed4a01ad7e5af764c0815a63ee35b81b91592503bf7ef1f7aedb`；原文件 mtime `2026-10-24T16:48:13.372504Z`。来源机器仍为 `pc-20260924rtuf-f11af23c08`，PID15032/出生Unix1792858804.978422，CK3 1.20.0.4/build25734779。冻结 c27 正式普通战役中通过正常切换角色转为玩家33702，装备自然「★君王之杖」，再进入正常管理决议；原生 `r35-context-manage-01` 的实际选项绑定物品295，`r35-listen-01` 后事件实例为2。

图中显示1级、经验0/100、嗜战、武器食性、共鸣20/100、丧钟合唱I，以及50威望/10压力/+25经验的训练选择和镇压90日入口。该图是直接采集的 JPEG 原件，无裁切、重绘或转码；没有把未执行的喂养或付费写成结果。R35 固定 hold 到期，native报告GREEN但 CK3进程1、public2、managed cleanup已证；未获正常退出资格，Save0、录像0。

随后追加第五张图库，并在正文“停手选择”段嵌图。第二批两次 SDK 原退出仍为0/0，最终五图正文7644 B。匿名公开 API 全文、网页唯一正文文字及五个图片地址、页面实际图库五个地址、原877字符/23行 Notes 全部匹配；第五图公开下载与源文件逐字节相同。原四图证据保留，第二批原始响应与验证结果位于 [state-b02](../../promo/living_artifacts/workshop-media-wip-20261024-a01/publication/state-b02/public-verification.json)。
