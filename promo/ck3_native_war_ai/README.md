# 《CK3 的 AI 为什么开战、绕路，又突然愿意讲和？》

**导演案 v1 · 2026-09-22 · 13 分 30 秒。** 从[导演案](director-plan.md)开始阅读。

这是面向 CK3 玩家的原生战争 AI 机制解说片。用一张持续演变的教学地图，串起宣战、军队目标、交战判断、求援和和平；研究基线为 CK3 **1.19.0.6**。本次交付导演与制作方案，现有研究结论保持原样。

| 文件 | 用途 |
| --- | --- |
| [director-plan.md](director-plan.md) | 选题、叙事、逐章处理、示范旁白、视听设计与补研取舍 |
| [shot-list.md](shot-list.md) | 21 个镜头组、调度、取材要求与替代画面 |
| [timeline.json](timeline.json) | 0–810 秒连续时间预算，镜头、章节和 claim ID 对应 |
| [claims.json](claims.json) | 可讲结论、原文位置、证据性质与禁止外推 |
| [source-lock.json](source-lock.json) | 本案实际引用的研究文件、基准 commit、逐文件 SHA-256 |
| [promo-project.json](promo-project.json) | 原生 `xar-promo ProjectConfig`，8 章均为 `planned` |
| [production-workflow.md](production-workflow.md) | 已用工具、版本与 run，以及后续 composer、取材、渲染和审片接入点 |
| [build-records/director-20260922-r1.json](build-records/director-20260922-r1.json) | 本次工具验证、内容检查与封存 run 索引；不是媒体构建报告 |

已接入工具链的 **ProjectConfig → start-run → preserve → validate** 阶段。正文、时间线和来源表进入独立 run 的不可变素材存储。项目 adapter/preset 名称是本案预留标识，composer 尚待制作阶段实现；当前没有执行 `xar-promo plan/build`，也没有录屏、配音或成片。

默认中文旁白、简中主字幕与英文副字幕，2560×1440 / 30 fps；810 秒是导演预算，包含片尾。逐句旁白、英文字幕和最终音乐选曲在制作阶段完成。所有过程资产留在 `D:/workspace/ck3_native_war_ai_promo_work/` 的独立 attempt 中，大体积媒体不进 Git。
