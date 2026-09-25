# 第 1 集 IndexTTS 正式审片版

本配置承接同题 EdgeTTS 草稿的 25 段已核对文案与 266 秒墨西拿原版实机净片。正式版使用用户于 2026-09-19 提供、先前《Project 因果律》已采用的参考声；IndexTTS 2.5 采用自然参考情感、`duration_factor=0.90`、`interval_silence=100 ms`、`lang=ZH`、文本规范化。参考声及合成 WAV 只保存在本机私有 attempt/run，不进 Git。

每段以完成回执绑定原稿 SHA、参考 WAV SHA、模型 revision、参数和实测音频时长。镜头与字幕按 WAV 重新排定，不沿用 EdgeTTS 时间戳。原版实机镜头按原速只使用已验 clean span；独立重放第 6 天后与原始研究回执数值分叉的标注继续保留。系列唯一配乐仍为 `Quiet Courtly Tension.wav`，固定 -17 dB、旁白 0 dB、无 ducking 和归一化。

新 run 使用开始时查询的最新正式 `xar-promo` wheel，保存版本与 SHA。输入、生成音频、渲染片段、最终混音、机器审核报告和失败 attempt 均保留。审核包含独立 ASR 对明显漏句/重复的筛查、全片音视频严格解码、媒体/时长绑定、章节和边界抽帧及视觉安全区复核。ASR 不是逐字听审；机器检查与 `xar-promo review` 包都不产生人工签核。

机器检查通过后，仅将最终 MP4 复制到既有 `OneDrive/CK3-War-AI-20260923` 同步文件夹，核对本地两份文件的字节与 SHA，再读取 OneDrive 客户端“已上传”状态；不触发其他云文件下载。用户收到后仍可对整片内容提出修改。正式版完成此流程后，再继续深层抽签与写回、增援、撤退和终局研究。
