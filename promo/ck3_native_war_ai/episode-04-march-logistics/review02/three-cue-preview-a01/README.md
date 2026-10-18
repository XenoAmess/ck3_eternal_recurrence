# Review02 三段局部预览的可复用入口

[preview-selection.json](preview-selection.json)是机器无关的**选择合同**，不是可以直接交给 `xar-promo start-run` 的 ProjectConfig，也不含另一台机器的绝对素材路径。完整 69 段项目意图继续取本仓 `review02/production-inputs-a03/` 的精确双语归档，由其既有 `materialize_inputs.py --output <新目录>` 生成 `project/promo-project.json`。实际三 cue run 的配置快照与归档成员同为 86060 B／SHA-256 `6cdc1e349826d607a9c2fe1fa17e3b50d770a3a246bd207ea323002487d48140`。不要重写 69 条中文配音、英文字幕或章结构来凑局部预览。

可复用 composer 仍是既有 `promo/ck3_native_war_ai/integration/src/war_ai_promo/episode04_review02_mixed_rough.py` 的 `war_ai_promo.episode04_review02_mixed_rough:compose`。[本次实物构建所用原补丁](composer-tail-hold-threads1.patch)精确保留为历史；[拟合回补丁](composer-tail-hold-threads1-multiwindow.patch)另修一个同 raw 多窗口的兼容回归：普通 `hold=0` 的不同窗口继续各自通过，仅 R204 `C01-01` 源帧 `[15,600)` 追加明确标记的 27 帧尾帧保持；FFmpeg 限制单线程供当次并发编译窗口。新补丁已经过同 raw、两个不同长度且 `hold=0` 的离线 planner 对照及 R204 保持分支对照，**没有重新构建或渲染旧三 cue MP4**；旧实物 RunManifest、QA 回执只绑定旧 producer。两个补丁都不是对以后任意短素材的通用补帧许可。上游渲染图 seam 有变化时检查会拒绝，须重新审补丁。

在另一台机器复用时，先从当前本机实际媒体和 69 段输入生成新的 `production-inputs-v1`：为 `metadata.measured/method/raster`、三个视频、选中音频与字幕分别提供**本机路径**及真实 byte/SHA，保留 artifact ID 和 cue 顺序，再用该机新 run 的 `preserve` 固定来源。`scene_token` 和逻辑 ID 只用于查找与沟通，不能据此拼出 C:/D:/ 路径。开始新 run 前按项目 AGENTS 和 promo skill 新查正式 release、核 wheel/requirements/installed 来源，取得该机容量准入；不能复用本场的 Steam、CK3、Defender、磁盘或运行时资格。

本机已成功的 Review02 局部预览与自动检查、机器绑定输入及有限视觉结果见[专题](../../../../../docs/ck3-native-ai/episode04-review02-three-cue-preview-12004.md)和其 evidence 索引。本合同仅用于继续视频制作/智能体选择素材，不授真实 R05/R06/ABC 业务结果、完整 69 段成片或人工签核。
