# 第四期 A-only 六章制作代码与结果

本目录保留实际制作代码、六章旁白/中英文配置和审阅版结果账。69段、实际口播26:19.176，画面47,376帧/1920×1080/30fps。A首次观测伦敦为第51日，到达区间(49,51]，不是精确到达时刻。B/C、胜者和实际付款账仍未知。

视频、原片、音频、字体、图片、字幕和运行日志继续留在外部资产目录，没有进入本包。项目配置和本目录校验使用相对文件；provenance内原回执的机器路径只描述实际历史，不作为便携校验依赖。

`e4_picture_producer.py`是实际通过check/render的a06准确源码，真实接口为`check`、`render`、`--input`、`--workdir`、`--preview-only`。它消费执行者明确绑定的外置输入；缺失/变化的引用失败，不自动查找素材。

`assemble_A_only.py`是本次新增的参数化入口，默认只读JSON元数据计划，不创建目录、不读取媒体。显式`--render`才复核准确输入、复用53个既有dry MOV、插入16个C05，再编码一次连续全局ASS、口播及唯一Quiet Courtly Tension配乐（固定−17dB，无ducking/normalize）。此参数化投影只验过help/default plan，不能冒称重新实际渲染；准确已执行源码保留在`provenance/actual-assembler-a01.py`。

```text
<verified-python> -B -X utf8 e4_picture_producer.py --help
<verified-python> -B -X utf8 assemble_A_only.py --input <external-picture-input> --stable-receipt <external-53-receipt> --increment-receipt <external-C05-receipt> --subtitle-delivery <external-subtitle-delivery> --old-claim-ledger <external-old-claims> --workdir <new-external-directory>
<verified-python> -I -S verify_portable.py
```

未来渲染前必须新查独立工具链最新正式Release并验证所选解释器；本次实际版本为0.2.1，wheel SHA保留在结果账。依赖型操作明确采用已验证主venv，不能静默使用缺依赖的裸解释器。

原实际项目快照的3句`subtitles.zh`保留旧文本，但新片实际ASS/音频已使用A-only正确文本。本新意图配置仅同步C05-03/15/16的中文字幕字段到实际旁白，且标明新字节投影；不改变原快照、成片、音频或时间。原中文/英文文字及69段实际样本时钟由`paragraph-state-and-clock.json`绑定。

源窗口有限抽帧可用、自动媒体检查、完整人工1×播放/听审分别记录。当前没有continuous-clean、最终人工签核、上传或正式成片完成信用。很多源片显示游戏暂停；没有循环源窗口、长静帧填充、帧hold或逐段音频静音。保留C06原剪点与新样本网格最多1帧偏差，整章和全片累计帧数准确，音轨/字幕连续使用实际PCM时钟。

后续B/C真实收口再新增带来源的C05增量，所有历史版本与失败attempt永久保留。本包不调用游戏、SDK、桌面、任务总线、安全设置或Git，也不上传OneDrive。
