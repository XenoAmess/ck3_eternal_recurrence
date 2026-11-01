# 第一期单句修正

`machine_id: 4-8e1c2f1861`。2026-11-01用户指定将“我可没把联军打服”改为**“我可没被联军打服”**。

本轮仅修改`v03-16c-realm-r3`这一句，重配对应Edge TTS旁白、更新字幕并重编码该场。其余18场复用上一版音频和已编码画面，不重拍、不启动游戏，也不顺手修改其它台词。修改后的完整原句为：

> 他们要讨的那个人先死在了宫里，我可没被联军打服。这把董卓就到这儿。

[完整旁白](narration.txt)、[精确修改要求](change-request.json)。上一版视频和来源快照保留，新增`edit-05`和独立run`edit05-001`。原段保持23.4秒，全片切点及19场镜头列表不变；[复用证明](wording-change-proof.json)与[Root差异检查](root-diff-check.json)确认只改1字、18段直接复用，字幕正文也只差这一字。

已交付本机根目录`episode01-dongzhuo-wording-fix-review.mp4`及同名前缀字幕、封面和简介。成片363.990364秒、42,032,673B，SHA256为`9b4bc1dc98229db8d59c80a558845f2a9120021f5df540ea0395cd91e0e86fad`。文件与字节绑定见[交付快照](delivery-snapshot.json)及[制作元数据](edit-metadata.json)。Root独立核对新文件SHA，并在337.5535秒实际成片帧确认字幕为“我可没被联军打服”。

Edge TTS仍为`zh-CN-YunjianNeural`／rate`-12%`／pitch`-8Hz`。新音频装入原时长，无截尾；原生plan/build、自动检查、全片解码及最终validate完成。人工签核保持null，单帧观察不替代人工完整观看。存储按本轮[准入](storage-admission.json)与[闭场](storage-close.json)记录，旧片未覆盖，无新增Game动作或日期，无外部上传。
