# 音频修复版交付（2026-10-04）

[视频](C:/Users/1/OneDrive/CK3-War-AI-20260923/超人强_越超人越强_宣传片_音频修复版_20261004_1cd9049a.mp4)，138.667 秒、1080p30fps，SHA-256 `1cd9049a95451a5bc8dde181416021970c145fe68e4b64c599e6b9d6620f52c9`，31,740,736 字节。

先用已授权的 OneDrive 桌面客户端上传这一个文件，UTC 2026-10-04T10:59:44.691777+00:00 确认 InSync/validated 全字节/modified=0，再检查该交付副本。没有下载其他云文件，没有向视频平台发布。

根因是分段旁白延时、裁切和 PTS 重置顺序错误，导致各段声音短于画面，九个转场产生约 0.685–1.365 秒的时间洞。旧片全片缺 8.833 秒实际音频。[原片诊断](old-a4-aac-gap-diagnosis.json)与[旧片反例 FAIL](old-a4-counterexample.json)保持原样。

新版从十段原始晓晓旁白生成连续无损时间线，一首 Suno 配乐固定增益，取消 10:1 侧链和最终动态响度调节，最后一次 AAC 编码。[修复设计](../../audio-revision-20261004.md)。

上传副本的 **30 项媒体/音频检查全部 PASS**：完整 6,656,000 个样本，零 AAC 时钟缺口，九个转场前后一秒无零洞；相对配乐母带的增益区间最大 **0.1876 dB**。编码音频与连续母带相关系数 0.999942，信号/误差比 39.33 dB；响度 -16.48 LUFS、峰值 -2.45 dBTP。[声音连续性](audio-continuity-check.json)。

H.264 画面字节全部保留，4160 个 video packet 的相对时间、大小、标记一致，28 个对应媒体时间的实际 PNG 帧逐字节相同。移除旧音频容器后，统一消除了原来的 +21.354ms 零点偏移；首次按绝对时间比较的 FAIL 被保留，后续按独立测出的精确偏移重新比较。根线程查看了实际成片 contact sheet，最终二维码正确。[画面验证](visual-identity-check.json)。

真正生产函数生成的十段音频独立 FFmpeg 回归全部达到精确计划样本数；普通全量重建路径也已修复。[生产路径回归](ten-scene-production-regression.json)。

新原生 run 使用本次查询确认的最新正式工具链 0.2.1，原始声音、三个无损母带、失败比较、命令、过程和新旧视频全部保留。[制作记录](production-report.json)、[过程保全](retention-receipt.json)。机器检查不产生人工 1× 全片听审签核；native review 继续 pending-human-review，signoff 为零。
