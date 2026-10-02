# 战争系列第3期：一座城究竟是怎样被攻下的？

本期用原版 CK3 1.20.0.3 的威廉围攻刘易斯案例，说明总工作量、每日推进、攻城器械、阶段事件、破口、强攻，以及占领后如何连接战争分数。9章、129段中文旁白、中英字幕，1920×1080、30fps、H.264/AAC；片长 **23分27.721秒**。与前期战争分数内容的衔接取两次审阅集合的保守并集，合计66.567秒，其余围城内容为本期新增。

成片为外置 `D:/ck3-war-episode03-20261002-a01/episode03-nativebuild-a09/CK3-War-AI-Episode03-Siege-BrownGold.mp4`，155,322,628字节，SHA-256：

```text
166E6C53FA6C9359F2BBD826A4E9E6A8A49B4A6AFAEC6218B32A7335BDD89B0B
```

最终媒体审计和 OneDrive 交付回执将在[交付记录](../../../../docs/handover/2026-10-03-war-episode03-delivery.md)中收口。完整人工1×观看及签核尚未提供；机器验证和AI画面抽检分别按其真实范围记录。现有 `project/README.md`、9份冻结输入及a08报告是当时版本，保留原字节，不用后续结果改写历史。

实机事实、截图和原片从[原生研究专题](../../../../docs/ck3-native-ai/episode03-william-lewes-live-2026-10-03.md)及[证据索引](../../../../docs/ck3-native-ai/episode03-william-lewes-evidence-index.json)查阅。过程资产永久保留在上述外置目录，MP4、录像、存档及音频不进Git。工具链采用独立仓库最新正式0.2.1 wheel，项目不vendoring通用包。

`production.py`负责本期中文旁白、板卡、字幕及逐帧时序；`composer.py`接入公开工具链；`tools/media_audit.py`核对编码后的音频、字幕像素与415个实际帧；`tools/delivery.py`只把选定的一个MP4送入既有OneDrive目录。a09复用a08全部编码画面和129份原始PCM，逐段补静音至帧边界后只编码一次最终AAC；a08的旁白尾句时序RED、失败审计及所有原素材继续保留。
