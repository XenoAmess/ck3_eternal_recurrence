# 《CK3 的 AI 为什么开战、绕路，又突然愿意讲和？》

**EdgeTTS 求援样片已生成 · 2026-09-23 · 3:58。** [制作与样片记录](production-stage.md)提供修正版媒体位置、构建收据与限制；[长篇导演案](longform/director-plan.md)保留完整 20–40 分钟的编排。约 30 分钟是参考，最终长度由逐句稿和旁白粗剪决定。

这是面向 CK3 玩家的原生战争 AI 机制解说片。三个完整教学案例围绕“选择战争、军队行动、和平”展开，使用同一张持续演变的地图；研究基线为 CK3 **1.19.0.6**。本次补充叙事、伸缩章节、风险与制作安排，现有研究结论保持原样。

| 文件 | 用途 |
| --- | --- |
| [longform/director-plan.md](longform/director-plan.md) | 三个案例、8 章伸缩预算、视听方式、风险与解决办法 |
| [longform/shot-list.md](longform/shot-list.md) | 45 个参考镜头组、调度、取材要求与替代画面；可以随逐句稿拆并 |
| [longform/timeline.json](longform/timeline.json) | 20–40 分钟工作范围、30 分钟参考节拍，镜头/章节/案例/claim ID 对应 |
| [longform/narration.md](longform/narration.md) / [JSON](longform/narration.json) | 90 条中英逐句稿，覆盖 45 镜头；既有研究结论保持不变 |
| [longform/narration-help-sample.json](longform/narration-help-sample.json) | 12 条求援章节样片稿；新声音 attempt 消费当前修订 |
| [production-stage.md](production-stage.md) | 声音、图解、实际构建、实机取材和 IndexTTS 的阶段记录 |
| [claims.json](claims.json) | 可讲结论、原文位置、证据性质与禁止外推 |
| [source-lock.json](source-lock.json) | 本案实际引用的研究文件、基准 commit、逐文件 SHA-256 |
| [promo-project.json](promo-project.json) | 当前原生 `xar-promo ProjectConfig`，8 章均为 `planned`；时长硬限制留空，宽松预算在长篇时间线中 |
| [production-workflow.md](production-workflow.md) | 已用工具、版本与 run，以及后续 composer、取材、渲染和审片接入点 |
| [build-records/longform-director-20260922-r1.json](build-records/longform-director-20260922-r1.json) | 长篇 authoring 验证与新封存 run 索引；不是媒体构建报告 |

项目 adapter/preset 和 composer 已在 [integration](integration/README.md) 实现。求援样片已完成真实配音及 `xar-promo plan/build`；具体最高阶段与媒体收据见[制作记录](production-stage.md)。导演 authoring、单章样片、完整影片和自然实机取材分别记录，不混用状态。

默认中文旁白、简中主字幕与英文副字幕，2560×1440 / 30 fps。20–40 分钟指影片长度，不是制作工期；不为凑整点拉长静帧或加快配音。首个样片先解决讲解与字幕，音乐尚未加入。每次新任务/run 使用最新正式 xar-promo；所有过程资产留在 `D:/workspace/ck3_native_war_ai_promo_work/` 的独立 attempt 中，大体积媒体不进 Git。

13:30 初案保留为历史：[导演案 v1](director-plan.md)、[旧镜头表](shot-list.md)、[旧时间线](timeline.json)、[首个 run 索引](build-records/director-20260922-r1.json)。版本升级记录见 [toolchain-latest-policy-20260922.json](build-records/toolchain-latest-policy-20260922.json)。旧 run 的配置快照与素材不受当前 ProjectConfig 修改影响。
