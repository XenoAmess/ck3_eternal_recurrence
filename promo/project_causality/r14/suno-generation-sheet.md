# 《Project 因果律：伪天司的辉煌愿景》r14 Suno 生成单

本文件对应 `53:52.292` 的 r14 无音乐审片版。项目所有者手动操作 Suno；任何自动化都不得登录或控制 Suno 网页。

## 第一轮只做什么

先生成 6 条章节母带，每条点击一次 Generate，保留 Suno 同时给出的 A/B 两个候选，共 12 个原始文件。第一轮不要 Continue、Remaster 或 Cover。待试听选出母带后，只对咒、罗贝尔、术、辉煌愿景的入选版本做 Continue。

## 通用设置

| 参数 | 设置 |
|---|---|
| Mode | Custom |
| Model | V5.5 优先；若账户没有则 V5 |
| Instrumental | On |
| Lyrics | 只放下列结构标签，不放说明文字或歌词 |
| Style Influence | 默认 80% |
| Weirdness | 默认 30% |
| Exclude Styles | 使用每轨给出的 4 项，不再追加 |
| 生成次数 | 每轨先生成 1 次，保留自动产生的 A/B 两版 |
| 下载 | WAV 或账户允许的最高原始质量；不要预先归一化、转码或降噪 |

Suno 没有精确时长参数。结构标签数量是主要时长控制手段；生成稍长后由后期裁切、交叉淡化和旁白 ducking 对齐。六条音乐共享“黑暗奇幻档案 + 克制机械脉冲 + 五音余烬母题”，但每章改变密度。

## 00 — Cold Open / Prologue

- 覆盖：`00:00–03:57`
- 目标生成长度：`04:20–05:15`
- Weirdness：35%
- Style Influence：80%

### Style Box

```text
Cinematic dark-fantasy chamber score, low strings, ancient bell, glass harmonics and restrained analog pulse. Slow 68 BPM, incomplete five-note ember motif, spacious documentary mix, wide dynamic range.
```

### Lyrics Box

```text
[Intro - cold unease]

[Main Theme - question awakens]

[Development - evidence emerges]

[Bridge - two paths open]

[Outro - threshold crossed]

[End]
```

### Exclude Styles

```text
no vocals
no choir
no EDM drop
no trailer braams
```

## 01 — Spell / Visible Products

- 覆盖：`03:57–14:29`
- 母带目标：`07:20–08:00`
- 后续：入选版本再 Continue 约 3–4 分钟
- Weirdness：30%
- Style Influence：82%

### Style Box

```text
Dark-fantasy orchestral documentary score, low strings, frame drums, hammered dulcimer and subtle analog pulse. 80 BPM, recurring five-note ember motif, measured forward motion, detailed spacious mix.
```

### Lyrics Box

```text
[Intro - covenant opens]

[Main Theme - artifacts revealed]

[Development - many forms]

[Interlude - inheritance deepens]

[Development - systems awaken]

[Bridge - proof over promise]

[Finale - visible result]

[Outro - controlled momentum]

[End]
```

### Exclude Styles

```text
no vocals
no choir
no heroic fanfare
no pop drums
```

## 02 — Robert / Autonomous Campaign

- 覆盖：`14:29–23:22`
- 母带目标：`07:20–08:00`
- 后续：入选版本再 Continue 约 1.5–2.5 分钟
- Weirdness：25%
- Style Influence：85%

### Style Box

```text
Medieval strategic documentary score, low-string ostinato, frame drums, muted brass and subtle analog pulse. 84 BPM, tactical progression, restrained tension, controlled victory lift, transparent mix.
```

### Lyrics Box

```text
[Intro - map awakens]

[Main Theme - ruler chosen]

[Development - realm assessed]

[Interlude - target weighed]

[Development - deliberate march]

[Bridge - controlled conflict]

[Finale - earned victory]

[Outro - campaign continues]

[End]
```

### Exclude Styles

```text
no vocals
no choir
no trailer braams
no action bombast
```

## 03 — Method / Production Chain

- 覆盖：`23:22–35:50`
- 母带目标：`07:20–08:00`
- 后续：入选版本再 Continue 约 4.5–5.5 分钟
- Weirdness：30%
- Style Influence：85%

### Style Box

```text
Orchestral-electronic process score, pizzicato low strings, paper percussion, modular synth pulse and dry metallic clicks. 88 BPM, five-note motif arranged as a precise workflow, clean separation, disciplined dynamics.
```

### Lyrics Box

```text
[Intro - blueprint measured]

[Main Theme - documents become contracts]

[Development - generators synchronize]

[Interlude - offline semantics]

[Development - state exposed]

[Break - visible evidence only]

[Bridge - release chain closes]

[Outro - methods return evidence]

[End]
```

### Exclude Styles

```text
no vocals
no cyberpunk aggression
no festival drums
no busy lead synth
```

## 04 — Principle / Evidence Has Weight

- 覆盖：`35:50–42:30`
- 目标生成长度：`06:30–07:20`
- Weirdness：20%
- Style Influence：88%

### Style Box

```text
Sparse dark chamber score, low cello, distant ancient bell and dry paper percussion. Slow 60 BPM, five-note motif reduced to isolated tones, severe pauses, intimate uncompressed mix.
```

### Lyrics Box

```text
[Intro - austere still]

[Main Theme - claims weighed]

[Interlude - post-state only]

[Bridge - hierarchy of evidence]

[Development - boundaries held]

[Outro - verdict suspended]

[End]
```

### Exclude Styles

```text
no vocals
no choir
no drum kit
no cinematic boom
```

## 05 — Radiant Vision / Recurrence

- 覆盖：`42:30–53:52`
- 母带目标：`07:20–08:00`
- 后续：入选版本再 Continue 约 3.5–4.5 分钟，并承担最终 CTA
- Weirdness：35%
- Style Influence：82%

### Style Box

```text
Visionary orchestral-electronic documentary finale, rising strings, glass harmonics, deep frame drums and luminous analog pulse. 82 BPM, five-note ember motif gradually completed, broad controlled arc, spacious mix.
```

### Lyrics Box

```text
[Intro - first loop ignites]

[Main Theme - four loops interlock]

[Development - evidence feeds creation]

[Interlude - human judgment remains]

[Development - results become causes]

[Bridge - retrospective luminous]

[Finale - disciplined ascent]

[Outro - recurrence continues]

[End]
```

### Exclude Styles

```text
no vocals
no choir
no EDM drop
no heroic fanfare
```

## 交回格式

两个候选都保留，不要只交自己更喜欢的一版：

```text
00-prologue-a.wav
00-prologue-b.wav
01-spell-a.wav
01-spell-b.wav
02-robert-a.wav
02-robert-b.wav
03-method-a.wav
03-method-b.wav
04-principle-a.wav
04-principle-b.wav
05-vision-a.wav
05-vision-b.wav
```

建议放入 `C:/Users/xenoa/OneDrive/Project因果律/音乐/inbox/`。同时保留每个候选的 Suno track ID 或分享 URL、实际模型版本、生成时间，以及生成账户在当时是否具备商业使用权。不要提交登录凭据。

## 第一轮淘汰标准

- 出现任何可辨认人声、吟唱或合唱：淘汰。
- 长时间满编制、持续抢旁白：淘汰。
- 通用企业凯旋、EDM drop、夸张 trailer braam：淘汰。
- 结尾突然截断、无法自然裁切：优先淘汰。
- Track 02 必须像真实策略推进，不像预告片大战；Track 04 必须是全片最稀疏的一首；Track 05 可以明亮，但不能变成英雄颂歌。

选出母带后，再为 01、02、03、05 分别指定 Continue 起点和续写标签。不要在母带选择前自行续写。
