# 《project因果律》项目所有者次日交接

## 1. 先审无音乐预演

本地文件：

```text
Z:\ck3_mod_rewrite\artifacts\project-causality\2026-09-19-r1\project-causality-820-nomusic-previz.mp4
```

请以 1× 从头连续观看一次。不要在第一次观看时逐帧挑错；先判断叙事是否成立，再按以下格式记录必须修改的时间码：

```text
02:38–02:56  家徽段：……
05:41–05:53  道章节：……
08:13–08:20  终幕：……
```

重点回答四件事：旁白声线是否保留、哪些静帧必须换成动态素材、字幕是否挡住关键 UI、四个 Loop 是否听完就能复述。

## 2. 再由你操作 Suno

当前执行者不会打开、登录或自动操作 Suno。请直接使用
[`music/suno-score-plan.md`](music/suno-score-plan.md) 中的 Style Box、结构标签和排除项，先生成主套曲候选；不要先把某条候选强行剪进时间线。

建议至少保留三个候选，并下载到：

```text
Z:\ck3_mod_rewrite\artifacts\project-causality\2026-09-19-r1\music\inbox\
├─ project-causality-score-a.*
├─ project-causality-score-b.*
└─ project-causality-score-c.*
```

如果可选，优先下载无损 WAV；否则保留 Suno 原始下载文件，不要先转码。每个候选同时记录：track ID 或分享 URL、模型版本、生成时间、
使用账户/方案对应的商业使用权状态。不要把登录凭据写进仓库。

## 3. 交回给后期

只需告诉后期：

- 保留哪一条主候选；
- 是否需要“道”章节的稀疏变奏和终幕 pickup；
- 候选文件的本地路径；
- 对应权利信息。

后期会在 picture lock 上完成裁切、循环点、闪避旁白、响度和峰值控制，再生成新的候选 SHA-256。音乐接入后，当前无音乐预演的签核资格
自动失效，必须重新完整审片。外部上传仍需另行明确授权。
