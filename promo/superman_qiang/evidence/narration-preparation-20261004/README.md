# 超人强旁白准备

状态：GREEN；声线 `zh-CN-XiaoxiaoNeural`；Edge TTS 7.2.8。

已生成 10/10 段，编码音频总时长 99.576 秒。旁白逐字采用已批准 02m 导演稿，rate +0%、pitch +0Hz、volume +0%。

原始工作目录：`C:/ck3-superman-qiang-promo-20261004/narration-prep-A0001`。请求、音频、句子时间标记、探测和命令日志均已保全进 `../../02m/runs/narration-prep-20261004-a01/run-manifest.json` 的 content-addressed storage。

[逐段音频、时长及 SHA-256](narration-summary.json)；[工具链与解释器版本](framework-version.json)；[原生 run 验证](run-validation.json)。

这是旁白准备结果；尚无成片或成片人工签核。后续剪辑以真实音频时长安排字幕、呼吸和片尾。

[逐段原文、文件校验和句子时间检查](verification.json) 已通过；十段原文均与批准的导演稿一致，音频、请求及边界文件的 30 项 SHA-256 一致。

后续剪辑直接复用汇总中的音频和句子时间文件，无需重新请求配音。若确需重新生成，使用新的 attempt/run 目录，旧文件继续保留。例如从仓库根目录执行：

```cmd
tools\.venv\Scripts\python.exe -X utf8 promo\superman_qiang\tools\prepare_narration.py --director promo\superman_qiang\02m\director.json --config promo\superman_qiang\02m\promo-project.json --work-dir C:\ck3-superman-qiang-promo-20261004\narration-prep-A0002 --run-directory promo\superman_qiang\02m\runs\narration-prep-20261004-a02 --run-id narration-prep-20261004-a02 --report-directory promo\superman_qiang\evidence\narration-preparation-20261004-a02
```
