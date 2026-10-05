# A-only 审阅版：独立完整解码追加

本追加绑定原成片准确身份：1,116,131,421 bytes，SHA-256 `fcd1f8587aabafbec2412e505f373795818ddd488c0b2d2b8b8f4428b16d78eb`。原15文件、六章配置、旧NULL字段及原成片全部准确保留；此记录不回填更早已有完整解码。

独立producer move_control只执行了一次全片视频与AAC严格解码，实际返回0并到progress end。视频47,376帧；AAC 74,025帧，每声道75,801,600样本/48kHz，均与期望一致，count差0。解码音频时长1579.2秒；原口播PCM1579.176秒与0.024秒最终网格尾差独立保留。NaN/Inf为0，总体峰值−3.098868 dBFS、RMS−22.357263 dBFS。这些是机器观察，不是听感评价。

**DECODE COUNTS PASS；EXACT AUDIO PTS CONTINUITY RED。** 音频PTS严格递增，但不是逐样本精确连续：5组相邻边界分别出现−1/+1样本，20个音频帧的绝对PTS偏移为−1样本。48kHz一个样本约20.833微秒。原因和可听影响都未实证，不能据此声称无问题或已证实听感异常，也不把误差容忍成精确连续PASS。

ROOT01初轮前缀解析漏计n4的RED、02精确连续断言失败及stdio继续原位置保全。ROOT03只重解析同一次sealed stderr，没有新解码、成片hash、ffprobe、原片或B live读取。本包只收录2份准确小JSON，不复制/读取电影、WAV、PCM、全stderr或大媒体。

原`project/actual-A-only-result.json`的历史whole-check NULL保持不变。此addendum及新a03 verifier是后来的独立追加。`provenance/final-machine-audit-ROOT03.json`与`final-machine-audit-findings03.json`分别保留准确原字节；其中机器路径只是历史定位，不是便携校验依赖。

没有完整人工1×播放、听审、连续源窗口clean、最终signoff、成片批准或上传信用。B/C与胜者仍NULL。入口和默认metadata plan未改，也没有重编码、重渲染或推断修复。

```text
<verified-python> -I -S verify_portable_audit_a03.py
```
