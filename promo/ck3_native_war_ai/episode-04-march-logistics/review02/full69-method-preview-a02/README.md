# Review02 69 段方法审阅版：三处纠错重编

本目录保存战争四期 Review02 方法版的一次**实际构建**、可复用的项目 composer 和小型证据。来源机器 `machine_id: desktop-3fevhd2-1c74096080`；实际媒体输入绑定 `65ce6ae5e55c0e8a855bebb6da3a1ccef08a711f`，原 69 段编码源绑定 `6a5a42eb563aa12951f9a0d16141146a9fdeec1d`。本机实际影片是 69 段／58,406 帧／1946.866667 秒，SHA-256 `8f7496f357b392504ee18c842b7a6b29f31eae81e8475ff8ec7c31ad3bed946b`；影片与原始素材**不在仓库**。

[project-binding.json](project-binding.json)给出跨机器的逻辑选择和本仓原 69 段配音、字幕、章结构的生成入口；[encoded-segment-map.json](encoded-segment-map.json)逐段列出精确编码源及本次输出 SHA。C05-09、C05-10、C05-14 重新编码，其余 66 段与原编码字节完全相同。三处显示纠错位于画面下缘，C05-10 的通用 PARTIAL 横标另移至不遮卡片标题的位置；旁白原字节不改。

`war_ai_promo/episode04_reuse_three_corrections.py` 和 `reuse_exact_segment.py` 是本场实际 producer 的精确源码。它们依赖已核的公共 `war_ai_promo.composer` 和正式 promo wheel；`evidence/source-index.machine-bound.json` 是**这台机器**的 RunManifest/CAS 精确绑定，代码会核 `machine_id`。其他机器应先从自己的原件和当前软件环境新建 Run、索引及 ProjectConfig，再按该机器实际路径和 SHA 重绑；不能把本场 C:/D:/ 路径、容量、安装或影片验收当作目标机器事实。原 69 段输入从仓库 `review02/production-inputs-a03/` 的归档经 `materialize_inputs.py --output <new-root>` 获得，避免为本包重复保存音轨和配置快照。

此版本只证明**方法版预览**实际生成并通过自动媒体检查：本机封存回执在 `evidence/`；严格解码、58,406 个单调 30fps 时间戳和三张成片帧 AI 抽查通过。首轮 QA 把 Windows CRLF 预审字幕与工具链 LF 产物作原始 SHA 比较，误报 RED；后续独立 a03 QA 仅修正换行比较，原失败回执保留。抽帧不等于整片连续人工 1 倍速观看。R05/R06/ABC 等 45 处关键动态镜头仍待合格素材；正式动态信用 0，不授签核、导出或发布。

`python -B -O verify_portable.py` 只验证本目录的小型索引、选择合同及回执相互一致，不读取本机大媒体，也不能替代原生 `xar_promo validate`、FFprobe/严格解码、人工 1 倍速审片或新机器资格。每个新 Run 仍须按项目规则重新查询正式工具链 Release、核 wheel/requirements/安装来源，取得容量准入并保留实际回执。
