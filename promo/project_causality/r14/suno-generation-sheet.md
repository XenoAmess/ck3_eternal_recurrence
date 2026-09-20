# 《Project 因果律：伪天司的辉煌愿景》r14 Suno 生成单

本文件对应 `53:52.292` 的 r14 无音乐审片版。项目所有者手动操作 Suno；任何自动化都不得登录或控制 Suno 网页。

## 第一轮只做什么

先生成 6 条章节母带，每条点击一次 Generate，保留 Suno 同时给出的 A/B 两个候选，共 12 个原始文件。第一轮不要 Continue、Remaster 或 Cover。待试听选出母带后，再对咒、罗贝尔、术、道、辉煌愿景的入选版本执行表内续写；其中“术”需要两次续写。每一次 Generate 或 Continue 的 Duration 都不超过 Suno 当前允许的 `06:00`。

## 通用设置

| 参数 | 设置 |
|---|---|
| Mode | Custom |
| Model | V5.5 优先；若账户没有则 V5 |
| Instrumental | On |
| Lyrics | 只放下列结构标签，不放说明文字或歌词 |
| Duration | 每次 Generate / Continue 填写下列唯一具体值；最高 `06:00` |
| Style Influence | 默认 80% |
| Weirdness | 默认 30% |
| Exclude Styles | 使用每轨给出的 4 项，不再追加 |
| 生成次数 | 每轨先生成 1 次，保留自动产生的 A/B 两版 |
| 下载 | WAV 或账户允许的最高原始质量；不要预先归一化、转码或降噪 |

当前 Suno 表单使用单一具体时长，且最高只能选择 `06:00`。下列 Duration 必须逐项照填；结构标签只负责段落与情绪弧线。续写从母带或上一段入选版本的指定时间开始，最终由后期裁切、交叉淡化和旁白 ducking 对齐。六条音乐共享“黑暗奇幻档案 + 克制机械脉冲 + 五音余烬母题”，但每章改变密度。

| Track | 成片覆盖 | 第一轮母带 | 第二阶段 Continue 1 | 第三阶段 Continue 2 | 可用总长 |
|---|---:|---:|---:|---:|---:|
| 00 — Cold Open / Prologue | `00:00–03:57` | `04:30` | 不续写 | 不续写 | `04:30` |
| 01 — Spell / Visible Products | `03:57–14:29` | `06:00` | 从 `05:40` 续写 `05:30` | 不续写 | `11:10` |
| 02 — Robert / Autonomous Campaign | `14:29–23:22` | `06:00` | 从 `05:40` 续写 `03:45` | 不续写 | `09:25` |
| 03 — Method / Production Chain | `23:22–35:50` | `06:00` | 从 `05:40` 续写 `06:00` | 从 `11:20` 续写 `02:00` | `13:20` |
| 04 — Principle / Evidence Has Weight | `35:50–42:30` | `06:00` | 从 `05:40` 续写 `01:30` | 不续写 | `07:10` |
| 05 — Radiant Vision / Recurrence | `42:30–53:52` | `06:00` | 从 `05:40` 续写 `06:00` | 不续写 | `11:40` |

表中的“可用总长”已经扣除了 Continue 起点前的重叠部分，不是把各次 Duration 简单相加；每章都留有裁切余量。

## 00 — Cold Open / Prologue

- 覆盖：`00:00–03:57`
- Duration：`04:30`
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
- 第一轮母带 Duration：`06:00`
- 第二阶段：从母带 `05:40` Continue，Duration：`05:30`
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

[Development - systems gathering]
```

### Exclude Styles

```text
no vocals
no choir
no heroic fanfare
no pop drums
```

### Continue 1 Lyrics Box

母带入选后，从 `05:40` 续写 `05:30`，Style Box 与 Exclude Styles 不变：

```text
[Continue - systems awaken]

[Development - many products converge]

[Bridge - proof over promise]

[Finale - visible result]

[Outro - controlled momentum]

[End]
```

## 02 — Robert / Autonomous Campaign

- 覆盖：`14:29–23:22`
- 第一轮母带 Duration：`06:00`
- 第二阶段：从母带 `05:40` Continue，Duration：`03:45`
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

[Development - decision commits]
```

### Exclude Styles

```text
no vocals
no choir
no trailer braams
no action bombast
```

### Continue 1 Lyrics Box

母带入选后，从 `05:40` 续写 `03:45`，Style Box 与 Exclude Styles 不变：

```text
[Continue - deliberate march]

[Development - battlefield adapts]

[Bridge - controlled conflict]

[Finale - earned victory]

[Outro - campaign continues]

[End]
```

## 03 — Method / Production Chain

- 覆盖：`23:22–35:50`
- 第一轮母带 Duration：`06:00`
- 第二阶段：从母带 `05:40` Continue，Duration：`06:00`
- 第三阶段：从 Continue 1 入选整曲的 `11:20` Continue，Duration：`02:00`
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

[Development - machinery turns]
```

### Exclude Styles

```text
no vocals
no cyberpunk aggression
no festival drums
no busy lead synth
```

### Continue 1 Lyrics Box

母带入选后，从 `05:40` 续写 `06:00`，Style Box 与 Exclude Styles 不变：

```text
[Continue - state exposed]

[Development - interfaces align]

[Break - visible evidence only]

[Development - release path measured]

[Interlude - verification waits]
```

### Continue 2 Lyrics Box

先选定 Continue 1 的 A/B；再从入选整曲的 `11:20` 续写 `02:00`，Style Box 与 Exclude Styles 不变：

```text
[Continue - final proof]

[Bridge - release chain closes]

[Outro - methods return evidence]

[End]
```

## 04 — Principle / Evidence Has Weight

- 覆盖：`35:50–42:30`
- 第一轮母带 Duration：`06:00`
- 第二阶段：从母带 `05:40` Continue，Duration：`01:30`
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
```

### Exclude Styles

```text
no vocals
no choir
no drum kit
no cinematic boom
```

### Continue 1 Lyrics Box

母带入选后，从 `05:40` 续写 `01:30`，Style Box 与 Exclude Styles 不变：

```text
[Continue - verdict forms]

[Outro - verdict suspended]

[End]
```

## 05 — Radiant Vision / Recurrence

- 覆盖：`42:30–53:52`
- 第一轮母带 Duration：`06:00`
- 第二阶段：从母带 `05:40` Continue，Duration：`06:00`，并承担最终 CTA
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

[Development - recurrence gathers]
```

### Exclude Styles

```text
no vocals
no choir
no EDM drop
no heroic fanfare
```

### Continue 1 Lyrics Box

母带入选后，从 `05:40` 续写 `06:00`，Style Box 与 Exclude Styles 不变：

```text
[Continue - results become causes]

[Development - four loops interlock]

[Bridge - retrospective luminous]

[Finale - disciplined ascent]

[Outro - recurrence continues]

[End]
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

选出母带后，严格按总表顺序续写：01=`05:30`，02=`03:45`，03=`06:00` 后再 `02:00`，04=`01:30`，05=`06:00`。所有单次 Duration 均不超过 `06:00`。每一步都先在 A/B 中选出入选版本，再从该版本继续；不要同时从两个候选分叉续写。
