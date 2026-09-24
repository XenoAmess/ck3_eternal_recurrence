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

用户试听后确认继续。第一批三段用独立 Whisper-base CPU 无提示转写做漏句筛查，字符相似度分别为 `0.6908 / 0.7410 / 0.8071`；各段结尾均转写到对应讲述的末句。相似度受专有词、数字、同音字和繁简差异影响，不能当作准确率或人工听审。后续使用 [独立语音筛查工具](integration/src/war_ai_promo/audit_index_speech.py)按原始音频与文案哈希绑定完整批次的回执，发现明显异常时再单段重做。

完整批次转写已在渲染前做宽松的完整性门禁：检查识别文本长度相对原稿没有大幅缩水或重复，且识别时间从开头覆盖至音频末尾附近。45 段均通过；这项门禁只筛查明显截断、静音和重复，不证明字词或数字逐字准确。例如 V3-06 的原稿与 IndexTTS 输入保留了“十万七千一百八十”，Whisper-base 把这个数字转写成 `17,180`，不能把转写误差反推为配音已逐字正确或错误。

IndexTTS 不提供可复用的 EdgeTTS 逐句时间戳。新版本按每段实测 WAV 时长与中文原稿各句的字数建立逐句估算区间，让一段旁白显示 4–8 组可读字幕，而不是约 50 秒仅分两块。该时序是估算，不是音素级对齐；英文字幕仍按文案比例分配。45 段结构性 dry run 检查了每组末尾与对应 WAV 时长一致；已抽看成片的研究卡、实机画面和字幕帧，人工 1× 全片听看仍待用户审阅。

实现入口为 [IndexTTS 批量合成器](integration/src/war_ai_promo/index_revoice.py)和[新时长与连续取材绑定器](integration/src/war_ai_promo/prepare_index_film.py)。旧 run 的状态和媒体均保留原样。

## 完整审阅片交付：2026-09-24

新 `v4-index-film-attempt-001` 将 45 段实际 WAV 重新排成八章，成片 **37:04.888**、2560×1440 / 30 fps、AAC 48 kHz 双声道，五段 CASE-W / CASE-C 实机镜头均按真实配音时长从已验干净区间重新截取，原速连续播放。最终 MP4 为 `228,899,890` 字节，SHA-256 `7be5bc37cda034f866bc8b5774edfc121bd5ba22c0134b9cc88d6fd2de0b96e2`。完整的工具版本、参考声绑定、语音筛查、章节、审阅包与媒体检查在 [v4 构建记录](build-records/v4-index-fullfilm-20260924-r1.json)。

原生 run 验证与全片严格音视频解码通过；106 张边界审阅帧已生成，人工签核状态仍为 `pending-human-review`。只把最终 `CK3-War-AI-V4-IndexTTS-Review-20260924.mp4` 放入预选的 OneDrive 交付目录，源与目标本地 SHA-256 一致，客户端活动中心明确回读“已上传到 CK3-War-AI-20260923”。未读取或下载其他云端文件内容。客户端回读证明报告上传成功，不是云端逐字节下载回验或全片人工审片。
