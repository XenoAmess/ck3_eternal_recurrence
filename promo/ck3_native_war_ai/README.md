# 《CK3 的 AI 为什么开战、绕路，又突然愿意讲和？》

**当前交付：加入全系列唯一主题音乐的第 0 集完整审阅版。** 片长 37:04.888，八章、45 段 IndexTTS 旁白、五段连续原版实机画面、双语字幕和播放器章节书签。主题音乐是用户提供的 `Quiet Courtly Tension.wav`；一首曲子循环铺底，旁白不降音量，音乐固定 -17 dB，不做随旁白变化的 ducking。新片 `CK3-War-AI-Episode-0-Series-Theme-Review-20260924.mp4` 与原曲 WAV 已由 OneDrive 桌面客户端上传到 `CK3-War-AI-20260923`；[v5 构建记录](build-records/v5-theme-fullfilm-20260924-r1.json)绑定精确字节和证据范围。画面、章节、研究边界及声音均承接 [v4 IndexTTS 母版](build-records/v4-index-fullfilm-20260924-r1.json)；人工 1× 全片审阅和签核待用户完成。旧片的[审片结论、研究清单与重做标准](../../docs/ck3-native-ai/war-video-research-rebuild-2026-09-23.md)仍是本次重制依据。

用户希望把更深入的内容逐集制作；[后续专题系列规划](series-roadmap.md)以单条原生决策链为一集，并列明各集尚需取得的实机证据及唯一主题音乐规则。本片保持全景片定位，不追认系列中尚未完成的研究。[合集无字概念图](concept-art/series-concept-960x540-v1.png)为 960×540 的视觉方向稿，已单独通过 OneDrive 客户端上传；系列正式名称仍待确定。

第 1 集 R7D→R7E 重剪中得到的开场、数字与实机对拍、系列配色和上传后审片规则，见[系列制作经验](docs/production-lessons-r7e.md)。

用户提供的参考声及 IndexTTS 重配过程见[重配音记录](index-revoice-20260923.md)。此前的 [v3 EdgeTTS 完整审阅版](build-records/v3-fullfilm-20260923-r1.json)保留为历史产物，不再是当前推荐审阅文件。

## 历史：初版导演材料与被退回的影片

**历史：被退回的 28:56 审片版。** OneDrive 固定目录内的 `CK3-War-AI-Full-Film-20260923.mp4` 是旧的纯教学图解片；[原构建记录](build-records/fullfilm-edge-20260923-r1.json)及[制作记录](production-stage.md)只保留其当时事实，不代表当前推荐审阅件。

这是最初面向 CK3 玩家拟定的原生战争 AI 机制解说方案。三个教学案例围绕“选择战争、军队行动、和平”展开，使用同一张持续演变的示意地图；研究基线为 CK3 **1.19.0.6**。该方案保留为历史输入，现有研究结论保持原样。

| 文件 | 用途 |
| --- | --- |
| [longform/director-plan.md](longform/director-plan.md) | 三个案例、8 章伸缩预算、视听方式、风险与解决办法 |
| [longform/shot-list.md](longform/shot-list.md) | 45 个参考镜头组、调度、取材要求与替代画面；可以随逐句稿拆并 |
| [longform/timeline.json](longform/timeline.json) | 20–40 分钟工作范围、30 分钟参考节拍，镜头/章节/案例/claim ID 对应 |
| [longform/narration.md](longform/narration.md) / [JSON](longform/narration.json) | 90 条中英逐句稿，覆盖 45 镜头；既有研究结论保持不变 |
| [longform/narration-help-sample.json](longform/narration-help-sample.json) | 12 条求援章节样片稿；新声音 attempt 消费当前修订 |
| [production-stage.md](production-stage.md) | 声音、图解、实际构建、实机取材和 IndexTTS 的阶段记录 |
| [indextts-installation.md](indextts-installation.md) | 独立 IndexTTS 安装、真实中文输出、WebUI 启动命令与性能；样片仍使用 EdgeTTS |
| [claims.json](claims.json) | 可讲结论、原文位置、证据性质与禁止外推 |
| [source-lock.json](source-lock.json) | 本案实际引用的研究文件、基准 commit、逐文件 SHA-256 |
| [promo-project.json](promo-project.json) | 当前原生 `xar-promo ProjectConfig`，8 章均为 `planned`；时长硬限制留空，宽松预算在长篇时间线中 |
| [production-workflow.md](production-workflow.md) | 已用工具、版本与 run，以及后续 composer、取材、渲染和审片接入点 |
| [build-records/longform-director-20260922-r1.json](build-records/longform-director-20260922-r1.json) | 长篇 authoring 验证与新封存 run 索引；不是媒体构建报告 |

项目 adapter/preset 和 composer 已在 [integration](integration/README.md) 实现。v4 原生 run 已完成 IndexTTS 配音绑定、`xar-promo plan/build/review`；审阅包包含 106 张边界帧，状态为 `pending-human-review`、`approval_granted=false`。最终媒体另经完整音视频解码。具体阶段和收据见[v4 构建记录](build-records/v4-index-fullfilm-20260924-r1.json)。导演 authoring、单章样片、旧完整影片和新片分别记录，不混用状态。

默认中文旁白、简中主字幕与英文副字幕，2560×1440 / 30 fps。20–40 分钟指影片长度，不是制作工期；不为凑整点拉长静帧或加快配音。v4 用 CK3 原版画面与纸面图解，未加音乐；五段实机均明确标为上下文，不能充当未拍到的自然 AI 因果结果。每次新任务/run 使用最新正式 xar-promo；所有过程资产留在 `D:/workspace/ck3_native_war_ai_promo_work/` 的独立 attempt 中，大体积媒体不进 Git。

13:30 初案保留为历史：[导演案 v1](director-plan.md)、[旧镜头表](shot-list.md)、[旧时间线](timeline.json)、[首个 run 索引](build-records/director-20260922-r1.json)。版本升级记录见 [toolchain-latest-policy-20260922.json](build-records/toolchain-latest-policy-20260922.json)。旧 run 的配置快照与素材不受当前 ProjectConfig 修改影响。

## 2026-09-23 研究后重制

当前拍摄和剪辑要求以 [导演案 v3](longform/director-plan-v3.md) 为准。旧片已被用户退回；旧稿和其技术检查仅保留历史身份。[33 条主张台账](research-first-claim-ledger-20260923.md) 及 CK3 1.19.0.6 专题文档支撑新版 45 cue；现有五段实机只覆盖局势和军队上下文，仍未拍到自然 AI 宣战、战斗战分或求和的完整因果链，影片依证据边界明示这一点。
