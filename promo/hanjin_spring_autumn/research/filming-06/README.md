# 第一期重新录音与字幕

2026-11-01用户明确“入库。你来继续拍摄第二期。”，本版已设为第一期当前入库版本；实际文件与SHA绑定见[入库记录](archive-record.json)。此记录不补称完整1倍速审阅或外部投稿。

`machine_id: 4-8e1c2f1861`。2026-11-01用户明确收窄范围：文案只做“郿国王”→“郿侯”的批量替换，重新录音和字幕，不做其它改写或画面处理。

以edit05的19场实际制作脚本执行字面替换，实际命中0次；不为制造修改而增加称号、扩写开局或删改原句。19场均重新调用Edge TTS，沿用`zh-CN-YunjianNeural`、`rate=-12%`、`pitch=-8Hz`，重新生成字幕并合成新片。原镜头、取景、源片段、切点及故事顺序保持；“我可没被联军打服”和结尾模组宣传保留。

当前交付为本机`C:/workspace/hanjin-spring-autumn-20261031/episode01-dongzhuo-title-corrected-review.mp4`，配套同名前缀`.srt`与`-narration.m4a`。精确字节、时长和制作结果见[交付快照](delivery-snapshot.json)，范围检查与19次实际Edge返回见[修订检查](revision-proof.json)，完整台词见[旁白](narration.txt)。旧版保留。

使用独立`edit-06/project/runs/edit06-001`；自动检查与解码结果仅证明所述技术条件，人工签核保持null。没有启动游戏、重拍剧情或外部上传。
