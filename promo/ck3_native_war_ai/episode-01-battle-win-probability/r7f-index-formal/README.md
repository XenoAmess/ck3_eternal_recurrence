# 第 1 集 R7F：用户声音的 IndexTTS 正式重配

R7F 冻结 [R7E 的 23 段文案与墨西拿同场实机取帧](../r7e-recut/README.md)，只重做配音、实际音频长度驱动的字幕/镜头/章节时间轴和最终混音。旧 EdgeTTS 成片、脚本、素材及签核状态保持历史原样。

声源采用用户在 2026-09-19 提供的参考音频所转出的 22.05 kHz 单声道 WAV，SHA-256 `061fe25b425752776da6c35eb2c634e2424239a8b5a2ea694bdee5a850e6d8b1`，保存在私有工作目录，不进 Git 或公开音轨。沿用同项目《Project 因果律》确认过的 `duration_factor=0.90`、`interval_silence=100 ms`、`ZH`、文本规范化与参考声自然情感；不启用 QwenEmotion。IndexTTS 2.5 安装目录 `D:/workspace/index-tts/` 为已合入 PR #795/#799 的本地提交 `5bb1a21d0add49e164e1438144e48da31bb34582`。本次实际启用 #795 的 `reference_device=cpu`，保持 #799 的 `reuse_spk_cond_for_emo=false`，避免改变此前确认的情感条件。[同机速度证据](../indextts-pr-795-799-benchmark.md)显示这个组合中的 #795 单项在短句测试里最快；正式长片另记录实际耗时，不从短测外推确定工期。

独立语音 attempt 为 `D:/workspace/ck3_native_war_ai_promo_work/episode01-r7f-index-voice-001/`；独立 promo run 和正式成片 attempt 为 `D:/workspace/ck3_native_war_ai_promo_work/episode01-r7f-index-formal-001/`。本次开始前查询到最新正式 xar-promo Release 为 `v0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；新 run 的 [ProjectConfig](project/promo-project.json)绑定该次制作意图。参考声、每段语音和 TTS 请求/回执在 run 中以精确文件身份保全；字幕时间以新 WAV 实测长度估算句界，不沿用 EdgeTTS 的逐句时间戳。

用户要求先试听的 `E1-F01` 和 `E1-F03` 两段原始 WAV 已单独复制到既有 OneDrive 选择性同步目录 `CK3-War-AI-20260923`，文件名分别为 `CK3-War-AI-Episode-1-R7F-IndexTTS-E1-F01.wav`、`CK3-War-AI-Episode-1-R7F-IndexTTS-E1-F03.wav`。两份客户端活动回读均为“已上传”；只复制这两份，不读取或下载其他云文件。独立 Whisper-base CPU 转写仅筛查明显缺句、静音和重复，两段通过；专名和数字的识别误差不构成逐字听审或用户签核。

正式 MP4 仍使用第 0 集棕金包装和系列唯一主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`。旁白保持 0 dB，音乐固定 -17 dB，不做 ducking。整片先生成并完整解码，再只上传 MP4 到同一 OneDrive 文件夹；客户端确认上传后，对该精确文件核验哈希、音视频流、23 章、字幕、安全区、开场关键秒帧、各章配色和完整解码。机器验收与抽帧不等于 1× 人工观看。

本次实际生成 23/23 段语音，总语音 1530.73 秒；模型推理 3093.12 秒，推理 RTF 2.02，含加载的墙钟时间 3278.00 秒。Whisper-base CPU 对全部 23 段做缺句、静音、重复的建议性筛查，23/23 通过；转写对数字和专名仍有误识，不能当成逐字准确性证明。实际成片 `CK3-War-AI-Episode-1-Messina-Original-IndexTTS-Formal-R7F-20260926.mp4` 时长 1544.821354 秒（25:44.82），113155622 字节，SHA-256 `14db0d74b349386cffdcc96e4db6f7cc6015dff9403ddcbfcd317985accba880`。

成片已单文件复制到既有 OneDrive 选择性同步目录 `CK3-War-AI-20260923`；私有 attempt 的 `onedrive-client-check-03.json` 显示该精确文件“已上传”。上传后才对 OneDrive 本地副本运行机器审核：哈希与构建回执一致，2560×1440、AAC 48 kHz 双声道、23 个章节、全片解码通过，184 个中文和 65 个英文字幕事件通过格式与两行上限检查；开场第 1/8/18/30 秒及 23 个章节共 27 帧通过棕金固定区域配色检查。已人工查看这些开场抽帧和四张章节总览图，未发现镜头漂向无关海域或蓝灰包装。上传副本音轨统计均值 -20.5 dB、峰值 -2.5 dB。以上仍不是 1× 全片人工观看或用户对音色、节奏的签核。

## 2026-09-26 音频勘误与新交付

用户指出初版约 21:24 的“折合六十二点七七……”重复。核对发现冻结句稿和字幕只有一次，但 IndexTTS 原始 C10 WAV 的短片段 ASR 连续识别到两次；初版的整段粗筛未标记它。初版文件与上述回执保留，不再作为推荐观看版本。新独立 attempt `episode01-r7f-index-formal-002/` 在 C10 两个零幅值点之间移除多说的 2.789161 秒；剪切外 PCM 与原文件逐样本一致，其他 22 段 WAV 不变。原音频、修复音频、短片段/整段识别、剪切清单及 23 段局部复读筛查均保存在私有 attempt；方法教训见[局部重复检查](../../docs/production-lessons-r7f-index-voice.md)。

重新渲染的 `CK3-War-AI-Episode-1-Messina-Original-IndexTTS-Formal-R7F-Corrected-20260926.mp4` 时长 1542.054688 秒（25:42.05），SHA-256 `404720a924b50b57f7cd88c8a3ba43021aee8c79b4f327fc327b6c797a88d5dc`。OneDrive 客户端显示该新文件已上传；**上传后**对该精确副本核验哈希、完整解码、23 章、字幕和 27 处画面配色均通过。独立从最终 MP4 的 C10 混音音轨截取片段并转写，只识别到一次 `62.77`；这仍是机器证据，不等于人耳 1× 全片签核。正式交付身份见[修复版构建记录](../../build-records/episode1-r7f-index-formal-corrected-20260926.json)。
