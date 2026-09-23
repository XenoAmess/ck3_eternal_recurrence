# 战争 AI 影片 IndexTTS 重配音

2026-09-23 开始。用户提供 40.405 秒 m4a 参考声，并指定复用同项目《Project 因果律》“咒 / 术 / 道 / 辉煌愿景”版本的声音设置，重配当前 [v3 完整审阅片](build-records/v3-fullfilm-20260923-r1.json)。用户声明是同一声音素材；旧项目的私人 WAV 未在本工作区，不能由文件字节推定两者相同。原参考音频及转码 WAV 仅保存在任务工作目录和 xar-promo 私有素材库，不进入 Git 或影片音轨。

## 冻结输入与设置

| 项 | 本次绑定 |
| --- | --- |
| 用户 m4a | SHA-256 `6138141c2ee9213b0d10503b9433ae6c6096a429da7bc30c5501aaa9c93a49b3`；48 kHz 双声道，40.405 秒 |
| 模型参考 WAV | 22.05 kHz 单声道 PCM16；SHA-256 `061fe25b425752776da6c35eb2c634e2424239a8b5a850e6d8b1`；由上述 m4a 用 ffmpeg 转换 |
| 模型与情感 | IndexTTS 2.5，源码 `ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c`；沿用参考声自然情感，不启用 QwenEmotion 文本情绪或随机情感向量 |
| 语速与句间 | `duration_factor=0.90`、`interval_silence=100 ms`、`lang=ZH`、文本规范化；依据 [因果律 r15 配置](../project_causality/r15/edit-config.json)与 [r16 说明](../project_causality/r16/README.md) |
| 成片音频 | IndexTTS 原始 WAV 为 22.05 kHz；正式视频混音输出仍按项目成片合同封装为 48 kHz，不把上采样称为增加源细节 |
| 宣传工具链 | 开始本次任务时核对最新正式 GitHub Release 为 `xar-promo-toolchain v0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；本工作区解释器 `--version` 一致 |

旧 v3 的 45 段中文文本、八章结构与证据边界不改。IndexTTS 的自然语速会改变每段的实际时长；新片按测得 WAV 重排镜头、字幕与章节。五段 CK3 原速录像只从已验证的 clean span 重新取连续时间窗，不循环、加速或冒充自然 AI 决策。新运行、失败素材和原 EdgeTTS 影片各自保留。

## 已取得的试配证据

独立 `v4-index-speech-attempt-001` 生成 `V3-01.wav`：52.334 秒、22.05 kHz 单声道、SHA-256 `a7fcc9959b9670a0e0e8a22e7f1f43409591976626c1c9ae61d17813df199460`。原 EdgeTTS 此段语音为 46.632 秒，因此不能直接把新音频塞进旧的 47.2 秒镜头。Whisper-base 无提示转写能覆盖本段主要叙述，但有数字、同音字与繁简转换偏差；这只作自动缺句筛查，不是听感签核。参考源、pilot WAV、单段收据和 ASR 回执已进入该 attempt 的 xar-promo 素材库。

`v4-index-speech-attempt-002` 已复用试配 WAV，使用同一模型实例合成余下 44 段。实际 6 GB GPU 启用了上游低显存分段，约 7 秒语音的一个片段需要约 2 分钟推理；完整批次预计数小时，不能把启动或一段成功写成整片完成。

## OneDrive 试听交付

按用户要求，先将试配段编码为 48 kHz 双声道 AAC 音频 `CK3-War-AI-IndexTTS-Voice-Sample-V3-01.m4a`，时长 52.334 秒、1,220,175 字节、SHA-256 `c0817a97fb446a67ae21d0da5de0f68c73d68529cb042ceb5008c333f74e1475`。编码仅做采样率、声道与格式转换，未再次修改语速或音高。只将该文件放入本机 OneDrive 固定交付目录 `CK3-War-AI-20260923`；源与目标文件哈希一致。OneDrive 客户端的活动中心明确显示该文件“已上传到 CK3-War-AI-20260923”。音频、复制回执和客户端回读已作为三个独立 artifact 存入试配 run。此状态证明客户端报告上传成功，不代替用户试听、声线认可或整片签核。

实现入口为 [IndexTTS 批量合成器](integration/src/war_ai_promo/index_revoice.py)和[新时长与连续取材绑定器](integration/src/war_ai_promo/prepare_index_film.py)。后续仍需核对全部 WAV、给实机镜头重选窗口、以最新 xar-promo 新建完整 render run、导出 48 kHz 视频、完整媒体检查和客户端上传。本页在取得结果时追加构建记录，不回写旧 run 的状态。
