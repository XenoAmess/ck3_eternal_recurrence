# 《CK3 的 AI 为什么开战、绕路，又突然愿意讲和？》

**导演案 v2 · 2026-09-22 · 20–40 分钟宽松范围。** 从[现行长篇导演案](longform/director-plan.md)开始阅读。约 30 分钟是编排参考，最终长度由逐句稿和旁白粗剪决定。

这是面向 CK3 玩家的原生战争 AI 机制解说片。三个完整教学案例围绕“选择战争、军队行动、和平”展开，使用同一张持续演变的地图；研究基线为 CK3 **1.19.0.6**。本次补充叙事、伸缩章节、风险与制作安排，现有研究结论保持原样。

| 文件 | 用途 |
| --- | --- |
| [longform/director-plan.md](longform/director-plan.md) | 三个案例、8 章伸缩预算、视听方式、风险与解决办法 |
| [longform/shot-list.md](longform/shot-list.md) | 45 个参考镜头组、调度、取材要求与替代画面；可以随逐句稿拆并 |
| [longform/timeline.json](longform/timeline.json) | 20–40 分钟工作范围、30 分钟参考节拍，镜头/章节/案例/claim ID 对应 |
| [claims.json](claims.json) | 可讲结论、原文位置、证据性质与禁止外推 |
| [source-lock.json](source-lock.json) | 本案实际引用的研究文件、基准 commit、逐文件 SHA-256 |
| [promo-project.json](promo-project.json) | 当前原生 `xar-promo ProjectConfig`，8 章均为 `planned`；时长硬限制留空，宽松预算在长篇时间线中 |
| [production-workflow.md](production-workflow.md) | 已用工具、版本与 run，以及后续 composer、取材、渲染和审片接入点 |
| [build-records/longform-director-20260922-r1.json](build-records/longform-director-20260922-r1.json) | 长篇 authoring 验证与新封存 run 索引；不是媒体构建报告 |

已接入工具链的 **ProjectConfig → start-run → preserve → validate** 阶段。正文、时间线和来源表进入独立 run 的不可变素材存储。项目 adapter/preset 名称是本案预留标识，composer 尚待制作阶段实现；当前没有执行 `xar-promo plan/build`，也没有录屏、配音或成片。

默认中文旁白、简中主字幕与英文副字幕，2560×1440 / 30 fps。20–40 分钟指影片长度，不是制作工期；不为凑整点拉长静帧或加快配音。逐句旁白、英文字幕和最终音乐选曲在制作阶段完成。每次新任务/run 使用最新正式 xar-promo；所有过程资产留在 `D:/workspace/ck3_native_war_ai_promo_work/` 的独立 attempt 中，大体积媒体不进 Git。

13:30 初案保留为历史：[导演案 v1](director-plan.md)、[旧镜头表](shot-list.md)、[旧时间线](timeline.json)、[首个 run 索引](build-records/director-20260922-r1.json)。版本升级记录见 [toolchain-latest-policy-20260922.json](build-records/toolchain-latest-policy-20260922.json)。旧 run 的配置快照与素材不受当前 ProjectConfig 修改影响。
